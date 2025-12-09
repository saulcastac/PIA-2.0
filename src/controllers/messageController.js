import { processMessageWithAI } from '../services/openaiService.js';
import { sendWhatsAppMessage, formatPhoneNumber } from '../services/twilioService.js';
import {
  checkAvailability,
  createReservation,
  getAvailableCourts,
  getAvailableTimeSlots,
  findReservationsByPhone,
  cancelReservation,
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

      case 'cancelar':
        responseMessage = await handleCancelIntent(from, aiResponse.datos);
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
  // Si falta información, pedirla de manera conversacional
  if (informacionFaltante.length > 0) {
    // Usar el mensaje de la IA si está disponible y es conversacional
    // Si no, crear uno proactivo
    const tieneDatosPrevios = datos.cancha || datos.fecha || datos.hora;
    
    if (tieneDatosPrevios) {
      // Ya tenemos algo de información, ser más específico
      const mensajes = [];
      
      if (informacionFaltante.includes('cancha') && !datos.cancha) {
        mensajes.push('¿En qué cancha te gustaría jugar? Tenemos: ' + Object.values(config.canchas).map(c => c.nombre).join(', '));
      }
      if (informacionFaltante.includes('fecha') && !datos.fecha) {
        mensajes.push('¿Para qué día te gustaría reservar? Puedes decirme "hoy", "mañana" o una fecha específica');
      }
      if (informacionFaltante.includes('hora') && !datos.hora) {
        mensajes.push('¿A qué hora te gustaría jugar?');
      }
      
      return `¡Perfecto! Para completar tu reserva solo necesito:\n\n${mensajes.map(m => `• ${m}`).join('\n')}\n\n¡Con esa información estaré listo para confirmar tu reserva! 🎾`;
    } else {
      // No tenemos información previa, ser más general pero amigable
      const faltantes = informacionFaltante.map(f => {
        switch (f) {
          case 'cancha':
            return 'qué cancha te gustaría';
          case 'fecha':
            return 'para qué día';
          case 'hora':
            return 'a qué hora';
          default:
            return f;
        }
      }).join(', ');

      return `¡Hola! Me encantaría ayudarte a reservar una cancha 🎾\n\nPara hacerlo, necesito saber ${faltantes}.\n\n¿Qué te parece si empezamos?`;
    }
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
    
    // Obtener componentes de fecha y hora
    const year = fecha.getFullYear();
    const month = fecha.getMonth();
    const day = fecha.getDate();
    const hours = hora.getHours();
    const minutes = hora.getMinutes();
    
    // Crear string ISO con la fecha y hora, especificando el offset de GMT-6
    // GMT-6 = UTC-6, así que el offset es -06:00
    // Formato: YYYY-MM-DDTHH:mm:ss-06:00
    const dateTimeString = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}T${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:00-06:00`;
    
    // Crear Date object - JavaScript automáticamente convierte a UTC
    // Ejemplo: "2025-12-09T10:00:00-06:00" se convierte a "2025-12-09T16:00:00Z" (UTC)
    // Esto es correcto: 10 AM GMT-6 = 4 PM UTC
    const startTime = new Date(dateTimeString);

    // SIEMPRE verificar disponibilidad ANTES de proceder con la reserva
    console.log(`🔍 Verificando disponibilidad para ${canchaId} el ${dateTimeString}`);
    const availability = await checkAvailability(canchaId, startTime, duracion);
    
    if (!availability.disponible) {
      console.log(`❌ Cancha no disponible: ${availability.razon}`);
      
      // Obtener horarios disponibles alternativos para la misma fecha
      const fecha = parseDate(datos.fecha);
      const timeSlots = await getAvailableTimeSlots(canchaId, fecha);
      const cancha = config.canchas[canchaId];
      const timezoneDisplay = config.server.timezone || 'America/Mexico_City';
      const fechaLocal = utcToZonedTime(new Date(startTime), timezoneDisplay);
      const fechaTexto = format(fechaLocal, "EEEE, d 'de' MMMM", { locale: es });
      
      let mensajeAlternativas = '';
      if (timeSlots.length > 0) {
        mensajeAlternativas = `\n\n✅ Horarios disponibles para ${cancha.nombre} el ${fechaTexto}:\n${timeSlots.slice(0, 8).map(slot => `🕐 ${slot}`).join('\n')}`;
      } else {
        // Si no hay horarios en esa cancha, sugerir otras canchas disponibles
        const otrasCanchas = await getAvailableCourts(startTime, duracion);
        if (otrasCanchas.length > 0) {
          mensajeAlternativas = `\n\n✅ Canchas disponibles en ese horario:\n${otrasCanchas.map(c => `🏸 ${c.nombre}`).join('\n')}`;
        }
      }
      
      return `❌ Lo siento, ${availability.razon}.${mensajeAlternativas}\n\n¿Te gustaría reservar en otro horario o cancha?`;
    }
    
    console.log(`✅ Cancha disponible, procediendo con la reserva`);

    // Crear la reserva (solo si está disponible)
    const reservation = await createReservation(
      canchaId,
      startTime,
      duracion,
      nombreCliente,
      from
    );

    const cancha = config.canchas[canchaId];
    const timezoneDisplay = config.server.timezone || 'America/Mexico_City';
    // startTime está en UTC, convertir de vuelta a GMT-6 para mostrar
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
           `Tu reserva ha sido registrada exitosamente. ¡Nos vemos en la cancha! 🎾`;
  } catch (error) {
    console.error('Error procesando reserva:', error);
    return `Lo siento, hubo un error al procesar tu reserva: ${error.message}.\n\n` +
           `Por favor, intenta de nuevo o contacta directamente con el establecimiento.`;
  }
}

/**
 * Maneja la intención de cancelar una reserva
 * @param {string} from - Número de teléfono del cliente
 * @param {Object} datos - Datos extraídos (puede incluir fecha, cancha, etc.)
 * @returns {Promise<string>} - Mensaje de respuesta
 */
async function handleCancelIntent(from, datos) {
  try {
    // Buscar reservas del cliente por su teléfono
    const reservas = await findReservationsByPhone(from);
    
    if (reservas.length === 0) {
      return `No encontré ninguna reserva activa asociada a tu número de teléfono.\n\n` +
             `¿Estás seguro de que tienes una reserva? Si la hiciste con otro número, por favor proporciona más detalles.`;
    }

    const timezone = config.server.timezone || 'America/Mexico_City';
    
    // Si el usuario especificó cancha o fecha, intentar filtrar
    let reservaACancelar = null;
    
    if (datos.cancha || datos.fecha) {
      const canchaId = datos.cancha ? mapCanchaNameToId(datos.cancha) : null;
      const fechaBuscada = datos.fecha ? parseDate(datos.fecha) : null;
      
      // Filtrar reservas que coincidan
      const reservasFiltradas = reservas.filter(reserva => {
        let coincide = true;
        
        if (canchaId && reserva.canchaId !== canchaId) {
          coincide = false;
        }
        
        if (fechaBuscada) {
          const reservaStart = new Date(reserva.start.dateTime || reserva.start.date);
          const reservaStartLocal = utcToZonedTime(reservaStart, timezone);
          const reservaFecha = new Date(reservaStartLocal.getFullYear(), reservaStartLocal.getMonth(), reservaStartLocal.getDate());
          const fechaBuscadaNormalizada = new Date(fechaBuscada.getFullYear(), fechaBuscada.getMonth(), fechaBuscada.getDate());
          
          if (reservaFecha.getTime() !== fechaBuscadaNormalizada.getTime()) {
            coincide = false;
          }
        }
        
        return coincide;
      });
      
      if (reservasFiltradas.length === 1) {
        reservaACancelar = reservasFiltradas[0];
      } else if (reservasFiltradas.length > 1) {
        // Múltiples reservas que coinciden con el filtro
        let mensaje = `Encontré ${reservasFiltradas.length} reservas que coinciden:\n\n`;
        reservasFiltradas.forEach((reserva, index) => {
          const startTime = new Date(reserva.start.dateTime || reserva.start.date);
          const startTimeLocal = utcToZonedTime(startTime, timezone);
          const fechaFormateada = format(startTimeLocal, "EEEE, d 'de' MMMM", { locale: es });
          const horaFormateada = format(startTimeLocal, 'HH:mm');
          mensaje += `${index + 1}. ${reserva.canchaNombre} - ${fechaFormateada} a las ${horaFormateada}\n`;
        });
        mensaje += `\nPor favor, especifica cuál quieres cancelar (por ejemplo: "la de las 10 AM").`;
        return mensaje;
      }
    }

    // Si hay múltiples reservas y no se especificó filtro, mostrar opciones
    if (!reservaACancelar && reservas.length > 1) {
      let mensaje = `Encontré ${reservas.length} reservas activas:\n\n`;
      
      reservas.forEach((reserva, index) => {
        const startTime = new Date(reserva.start.dateTime || reserva.start.date);
        const startTimeLocal = utcToZonedTime(startTime, timezone);
        const fechaFormateada = format(startTimeLocal, "EEEE, d 'de' MMMM", { locale: es });
        const horaFormateada = format(startTimeLocal, 'HH:mm');
        
        mensaje += `${index + 1}. ${reserva.canchaNombre} - ${fechaFormateada} a las ${horaFormateada}\n`;
      });
      
      mensaje += `\nPor favor, especifica cuál reserva quieres cancelar (por ejemplo: "la de mañana" o "la de MONEX").`;
      
      return mensaje;
    }

    // Si hay solo una reserva o se identificó una específica, proceder a cancelarla
    if (!reservaACancelar) {
      reservaACancelar = reservas[0];
    }
    
    const canchaId = reservaACancelar.canchaId;
    const eventId = reservaACancelar.id;
    
    // Cancelar la reserva
    await cancelReservation(canchaId, eventId);
    
    const startTime = new Date(reservaACancelar.start.dateTime || reservaACancelar.start.date);
    const startTimeLocal = utcToZonedTime(startTime, timezone);
    const fechaFormateada = format(startTimeLocal, "EEEE, d 'de' MMMM 'de' yyyy", { locale: es });
    const horaFormateada = format(startTimeLocal, 'HH:mm');
    
    // Limpiar datos de la conversación
    updateConversationData(from, { reserva_cancelada: true });
    
    return `✅ Reserva cancelada exitosamente\n\n` +
           `📅 Fecha: ${fechaFormateada}\n` +
           `🕐 Hora: ${horaFormateada}\n` +
           `🏸 Cancha: ${reservaACancelar.canchaNombre}\n\n` +
           `Tu reserva ha sido cancelada. Si cambias de opinión, estaré aquí para ayudarte a hacer una nueva reserva. 🎾`;
  } catch (error) {
    console.error('Error cancelando reserva:', error);
    return `Lo siento, hubo un error al cancelar tu reserva: ${error.message}.\n\n` +
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
 * Parsea una fecha desde diferentes formatos, incluyendo fechas relativas
 * @param {string} dateString - String de fecha
 * @returns {Date}
 */
function parseDate(dateString) {
  if (!dateString) {
    const timezone = config.server.timezone || 'America/Mexico_City';
    return utcToZonedTime(new Date(), timezone);
  }

  const timezone = config.server.timezone || 'America/Mexico_City';
  const now = utcToZonedTime(new Date(), timezone);
  
  // Manejar fechas relativas
  const dateLower = dateString.toLowerCase().trim();
  
  if (dateLower === 'hoy' || dateLower === 'today') {
    return now;
  }
  
  if (dateLower === 'mañana' || dateLower === 'tomorrow' || dateLower === 'mañana' || dateLower === 'mañ') {
    return addDays(now, 1);
  }
  
  if (dateLower === 'pasado mañana' || dateLower === 'day after tomorrow') {
    return addDays(now, 2);
  }
  
  // Intentar diferentes formatos de fecha
  const formats = ['yyyy-MM-dd', 'dd/MM/yyyy', 'dd-MM-yyyy', 'yyyy/MM/dd'];
  
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
 * Parsea una hora desde diferentes formatos (24h y 12h con AM/PM)
 * @param {string} timeString - String de hora
 * @returns {Date}
 */
function parseTime(timeString) {
  if (!timeString) {
    const timezone = config.server.timezone || 'America/Mexico_City';
    const now = utcToZonedTime(new Date(), timezone);
    now.setHours(now.getHours() + 1, 0, 0, 0); // Hora siguiente por defecto
    return now;
  }

  const timeLower = timeString.toLowerCase().trim();
  let hours = 12;
  let minutes = 0;
  let isPM = false;

  // Detectar formato AM/PM
  if (timeLower.includes('am') || timeLower.includes('pm') || timeLower.includes('a.m') || timeLower.includes('p.m')) {
    isPM = timeLower.includes('pm') || timeLower.includes('p.m');
    
    // Extraer números
    const numbers = timeLower.match(/\d+/g);
    if (numbers && numbers.length > 0) {
      hours = parseInt(numbers[0]);
      minutes = numbers.length > 1 ? parseInt(numbers[1]) : 0;
      
      // Convertir a formato 24 horas
      if (isPM && hours !== 12) {
        hours += 12;
      } else if (!isPM && hours === 12) {
        hours = 0;
      }
    }
  } else {
    // Formato 24 horas: HH:mm o HHmm
    const cleaned = timeLower.replace(/[^\d:]/g, '');
    const parts = cleaned.split(':');
    
    if (parts.length === 2) {
      hours = parseInt(parts[0]) || 12;
      minutes = parseInt(parts[1]) || 0;
    } else if (cleaned.length >= 2) {
      hours = parseInt(cleaned.slice(0, 2)) || 12;
      minutes = cleaned.length >= 4 ? parseInt(cleaned.slice(2, 4)) : 0;
    }
  }

  // Validar rango
  hours = Math.max(0, Math.min(23, hours));
  minutes = Math.max(0, Math.min(59, minutes));

  const date = new Date();
  date.setHours(hours, minutes, 0, 0);
  return date;
}

