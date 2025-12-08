import { processMessageWithAI } from '../services/openaiService.js';
import { sendWhatsAppMessage, formatPhoneNumber } from '../services/twilioService.js';
import {
  checkAvailability,
  createReservation,
  getAvailableCourts,
  getAvailableTimeSlots,
} from '../services/calendarService.js';
import { config } from '../config/config.js';
import { parse, format, addDays, isToday, isTomorrow } from 'date-fns';
import { utcToZonedTime, zonedTimeToUtc, formatInTimeZone } from 'date-fns-tz';
import es from 'date-fns/locale/es/index.js';
import {
  getConversation,
  updateConversationData,
  addMessageToHistory,
  getMessageHistory,
  getConversationData,
} from '../utils/conversationMemory.js';

/**
 * Procesa un mensaje entrante de WhatsApp
 * @param {string} from - Número de teléfono del remitente
 * @param {string} messageBody - Contenido del mensaje
 * @returns {Promise<void>}
 */
export async function handleIncomingMessage(from, messageBody) {
  try {
    console.log(`Mensaje recibido de ${from}: ${messageBody}`);

    // Obtener o crear conversación
    const conversation = getConversation(from);
    
    // Agregar mensaje del usuario al historial
    addMessageToHistory(from, 'user', messageBody);

    // Obtener datos previos y historial de la conversación
    const previousData = getConversationData(from);
    const messageHistory = getMessageHistory(from);

    // Obtener contexto adicional (canchas disponibles, etc.)
    const context = await buildContext();

    // Procesar mensaje con IA (incluyendo historial y datos previos)
    const aiResponse = await processMessageWithAI(
      messageBody,
      context,
      messageHistory,
      previousData
    );
    
    // Fusionar datos nuevos con los previos
    const mergedData = {
      ...previousData,
      ...aiResponse.datos,
    };
    
    // Actualizar datos de la conversación
    updateConversationData(from, mergedData);

    // Procesar según la intención
    let responseMessage = aiResponse.mensaje_respuesta;

    switch (aiResponse.intencion) {
      case 'reservar':
        responseMessage = await handleReservationIntent(
          from,
          aiResponse.datos,
          aiResponse.informacion_faltante
        );
        break;

      case 'consultar_horarios':
        responseMessage = await handleScheduleQuery(aiResponse.datos);
        break;

      case 'consultar_canchas':
        responseMessage = await handleCourtsQuery(aiResponse.datos);
        break;

      case 'otra_consulta':
      default:
        // Usar el mensaje de respuesta de la IA
        break;
    }

    // Agregar respuesta del asistente al historial
    addMessageToHistory(from, 'assistant', responseMessage);
    
    // Enviar respuesta
    await sendWhatsAppMessage(formatPhoneNumber(from), responseMessage);
  } catch (error) {
    console.error('Error procesando mensaje:', error);
    const errorMessage =
      'Lo siento, hubo un error procesando tu solicitud. Por favor, intenta de nuevo o contacta directamente con el establecimiento.';
    await sendWhatsAppMessage(formatPhoneNumber(from), errorMessage);
  }
}

/**
 * Construye el contexto adicional para la IA
 * @returns {Promise<Object>}
 */
async function buildContext() {
  try {
    const timezone = config.server.timezone || 'America/Mexico_City';
    const nowUTC = new Date();
    const now = utcToZonedTime(nowUTC, timezone);
    const tomorrow = addDays(now, 1);
    const availableCourts = await getAvailableCourts(now, config.establecimiento.duracionDefault);

    return {
      canchasDisponibles: availableCourts.length > 0
        ? availableCourts.map(c => c.nombre).join(', ')
        : 'No hay canchas disponibles en este momento',
      fechaActual: format(now, 'yyyy-MM-dd'),
    };
  } catch (error) {
    console.error('Error construyendo contexto:', error);
    return {};
  }
}

/**
 * Mapea un nombre de cancha a su ID correspondiente
 * @param {string} canchaNameOrId - Nombre o ID de la cancha
 * @returns {string} - ID de la cancha
 */
function mapCanchaNameToId(canchaNameOrId) {
  if (!canchaNameOrId) {
    return Object.keys(config.canchas)[0];
  }
  
  // Si ya es un ID válido, retornarlo
  if (config.canchas[canchaNameOrId]) {
    return canchaNameOrId;
  }
  
  // Mapeo de nombres comunes a IDs
  const nameMap = {
    'monex': 'cancha_1',
    'gocsa': 'cancha_2',
    'teds': 'cancha_3',
    'woodward': 'cancha_4',
  };
  
  const normalizedName = canchaNameOrId.toLowerCase().trim();
  
  // Buscar por nombre en el mapa
  if (nameMap[normalizedName]) {
    return nameMap[normalizedName];
  }
  
  // Buscar por nombre en las canchas configuradas
  for (const [id, cancha] of Object.entries(config.canchas)) {
    if (cancha.nombre.toLowerCase() === normalizedName) {
      return id;
    }
  }
  
  // Si no se encuentra, retornar la primera cancha por defecto
  return Object.keys(config.canchas)[0];
}

/**
 * Maneja la intención de reservar
 * @param {string} from - Número de teléfono del cliente
 * @param {Object} datos - Datos extraídos de la reserva
 * @param {Array} informacionFaltante - Información que falta
 * @returns {Promise<string>} - Mensaje de respuesta
 */
async function handleReservationIntent(from, datos, informacionFaltante) {
  // Si falta información, pedirla
  if (informacionFaltante.length > 0) {
    const faltantes = informacionFaltante.map(f => {
      switch (f) {
        case 'cancha':
          return 'la cancha';
        case 'fecha':
          return 'la fecha';
        case 'hora':
          return 'la hora';
        default:
          return f;
      }
    }).join(', ');

    return `Para realizar tu reserva, necesito la siguiente información: ${faltantes}.\n\n` +
           `Por favor, proporciona estos datos y podré completar tu reserva.`;
  }

  // Validar y procesar la reserva
  try {
    // Mapear nombre de cancha a ID si es necesario
    let canchaId = datos.cancha || Object.keys(config.canchas)[0];
    canchaId = mapCanchaNameToId(canchaId);
    const fecha = parseDate(datos.fecha);
    const hora = parseTime(datos.hora);
    const duracion = datos.duracion || config.establecimiento.duracionDefault;
    const nombreCliente = datos.nombre_cliente || 'Cliente';

    // Combinar fecha y hora en la zona horaria correcta (GMT-6)
    const timezone = config.server.timezone || 'America/Mexico_City';
    const startTimeLocal = new Date(fecha);
    startTimeLocal.setHours(hora.getHours(), hora.getMinutes(), 0, 0);
    // Convertir a UTC para las operaciones (Google Calendar usa UTC internamente)
    const startTime = zonedTimeToUtc(startTimeLocal, timezone);

    // Verificar disponibilidad
    const availability = await checkAvailability(canchaId, startTime, duracion);
    
    if (!availability.disponible) {
      return `Lo siento, ${availability.razon}.\n\n` +
             `¿Te gustaría consultar otros horarios disponibles?`;
    }

    // Crear la reserva
    const reservation = await createReservation(
      canchaId,
      startTime,
      duracion,
      nombreCliente,
      from
    );

    const cancha = config.canchas[canchaId];
    const timezoneDisplay = config.server.timezone || 'America/Mexico_City';
    // Convertir de vuelta a la zona horaria local para mostrar
    const startTimeLocalDisplay = utcToZonedTime(startTime, timezoneDisplay);
    const fechaFormateada = format(startTimeLocalDisplay, "EEEE, d 'de' MMMM 'de' yyyy", { locale: es });
    const horaFormateada = format(startTimeLocalDisplay, 'HH:mm');

    // Marcar reserva como completada y limpiar datos de la conversación
    updateConversationData(from, { reserva_completada: true });

    return `✅ ¡Reserva confirmada!\n\n` +
           `📅 Fecha: ${fechaFormateada}\n` +
           `🕐 Hora: ${horaFormateada}\n` +
           `⏱️ Duración: ${duracion} minutos\n` +
           `🏸 Cancha: ${cancha.nombre}\n` +
           `👤 Cliente: ${nombreCliente}\n\n` +
           `Tu reserva ha sido registrada exitosamente. ¡Te esperamos!`;
  } catch (error) {
    console.error('Error procesando reserva:', error);
    return `Lo siento, hubo un error al procesar tu reserva: ${error.message}.\n\n` +
           `Por favor, intenta de nuevo o contacta directamente con el establecimiento.`;
  }
}

/**
 * Maneja consultas sobre horarios
 * @param {Object} datos - Datos extraídos
 * @returns {Promise<string>}
 */
async function handleScheduleQuery(datos) {
  try {
    const fecha = datos.fecha ? parseDate(datos.fecha) : new Date();
    const canchaId = datos.cancha || Object.keys(config.canchas)[0];

    const timeSlots = await getAvailableTimeSlots(canchaId, fecha);
    const cancha = config.canchas[canchaId];

    let fechaTexto = '';
    if (isToday(fecha)) {
      fechaTexto = 'hoy';
    } else if (isTomorrow(fecha)) {
      fechaTexto = 'mañana';
    } else {
      fechaTexto = format(fecha, "EEEE, d 'de' MMMM", { locale: es });
    }

    if (timeSlots.length === 0) {
      return `No hay horarios disponibles para ${cancha.nombre} el ${fechaTexto}.\n\n` +
             `Horario del establecimiento: ${config.establecimiento.horarioApertura} - ${config.establecimiento.horarioCierre}`;
    }

    return `Horarios disponibles para ${cancha.nombre} el ${fechaTexto}:\n\n` +
           timeSlots.map(slot => `🕐 ${slot}`).join('\n') +
           `\n\nHorario del establecimiento: ${config.establecimiento.horarioApertura} - ${config.establecimiento.horarioCierre}`;
  } catch (error) {
    console.error('Error consultando horarios:', error);
    return `Horario del establecimiento: ${config.establecimiento.horarioApertura} - ${config.establecimiento.horarioCierre}`;
  }
}

/**
 * Maneja consultas sobre canchas disponibles
 * @param {Object} datos - Datos extraídos
 * @returns {Promise<string>}
 */
async function handleCourtsQuery(datos) {
  try {
    const fecha = datos.fecha ? parseDate(datos.fecha) : new Date();
    const hora = datos.hora ? parseTime(datos.hora) : new Date();
    const duracion = datos.duracion || config.establecimiento.duracionDefault;

    const startTime = new Date(fecha);
    startTime.setHours(hora.getHours(), hora.getMinutes(), 0, 0);

    const availableCourts = await getAvailableCourts(startTime, duracion);

    if (availableCourts.length === 0) {
      return `No hay canchas disponibles en ese horario.\n\n` +
             `¿Te gustaría consultar otros horarios?`;
    }

    return `Canchas disponibles:\n\n` +
           availableCourts.map(c => `🏸 ${c.nombre}`).join('\n') +
           `\n\n¿Te gustaría reservar alguna?`;
  } catch (error) {
    console.error('Error consultando canchas:', error);
    const canchasList = Object.values(config.canchas).map(c => c.nombre).join(', ');
    return `Canchas disponibles en ${config.establecimiento.nombre}:\n\n${canchasList}`;
  }
}

/**
 * Parsea una fecha desde diferentes formatos
 * @param {string} dateString - String de fecha
 * @returns {Date}
 */
function parseDate(dateString) {
  if (!dateString) {
    const timezone = config.server.timezone || 'America/Mexico_City';
    return utcToZonedTime(new Date(), timezone);
  }

  // Intentar diferentes formatos
  const formats = ['yyyy-MM-dd', 'dd/MM/yyyy', 'dd-MM-yyyy', 'yyyy/MM/dd'];
  const timezone = config.server.timezone || 'America/Mexico_City';
  const now = utcToZonedTime(new Date(), timezone);
  
  for (const fmt of formats) {
    try {
      const parsed = parse(dateString, fmt, now);
      if (!isNaN(parsed.getTime())) {
        // Asegurarse de que la fecha esté en la zona horaria local
        return parsed;
      }
    } catch (e) {
      continue;
    }
  }

  // Si no se puede parsear, usar fecha actual en zona horaria local
  return utcToZonedTime(new Date(), timezone);
}

/**
 * Parsea una hora desde diferentes formatos
 * @param {string} timeString - String de hora
 * @returns {Date}
 */
function parseTime(timeString) {
  if (!timeString) {
    const now = new Date();
    now.setHours(now.getHours() + 1, 0, 0, 0); // Hora siguiente por defecto
    return now;
  }

  // Formato HH:mm o HHmm
  const cleaned = timeString.replace(/[^\d:]/g, '');
  const [hours, minutes] = cleaned.split(':').length === 2
    ? cleaned.split(':')
    : [cleaned.slice(0, 2), cleaned.slice(2, 4)];

  const date = new Date();
  date.setHours(parseInt(hours) || 12, parseInt(minutes) || 0, 0, 0);
  return date;
}

