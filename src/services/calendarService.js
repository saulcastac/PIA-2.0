import { google } from 'googleapis';
import { config } from '../config/config.js';
import { format, parseISO, addMinutes, isBefore, isAfter } from 'date-fns';
import { utcToZonedTime, zonedTimeToUtc, formatInTimeZone } from 'date-fns-tz';

let calendarClient = null;

/**
 * Inicializa el cliente de Google Calendar
 */
export function initializeCalendar() {
  const oauth2Client = new google.auth.OAuth2(
    config.googleCalendar.clientId,
    config.googleCalendar.clientSecret,
    config.googleCalendar.redirectUri
  );

  oauth2Client.setCredentials({
    refresh_token: config.googleCalendar.refreshToken,
  });

  calendarClient = google.calendar({ version: 'v3', auth: oauth2Client });
  console.log('Cliente de Google Calendar inicializado');
}

/**
 * Obtiene las reservas de una cancha en un rango de fechas
 * @param {string} canchaId - ID de la cancha
 * @param {Date} startDate - Fecha de inicio
 * @param {Date} endDate - Fecha de fin
 * @returns {Promise<Array>} - Lista de eventos/reservas
 */
export async function getReservations(canchaId, startDate, endDate) {
  if (!calendarClient) {
    initializeCalendar();
  }

  const cancha = config.canchas[canchaId];
  if (!cancha) {
    throw new Error(`Cancha ${canchaId} no encontrada`);
  }

  try {
    // Convertir fechas a UTC para la consulta
    const timezone = config.server.timezone || 'America/Mexico_City';
    const startDateUTC = zonedTimeToUtc(startDate, timezone);
    const endDateUTC = zonedTimeToUtc(endDate, timezone);

    const response = await calendarClient.events.list({
      calendarId: cancha.calendarId,
      timeMin: startDateUTC.toISOString(),
      timeMax: endDateUTC.toISOString(),
      singleEvents: true,
      orderBy: 'startTime',
      timeZone: timezone,
    });

    // Convertir las fechas de las reservas de vuelta a la zona horaria local
    const items = (response.data.items || []).map(item => {
      if (item.start.dateTime) {
        const startUTC = new Date(item.start.dateTime);
        const endUTC = new Date(item.end.dateTime);
        item.start.dateTime = utcToZonedTime(startUTC, timezone).toISOString();
        item.end.dateTime = utcToZonedTime(endUTC, timezone).toISOString();
      }
      return item;
    });

    return items;
  } catch (error) {
    console.error(`Error obteniendo reservas para ${canchaId}:`, error);
    throw error;
  }
}

/**
 * Verifica si una cancha está disponible en un horario específico
 * @param {string} canchaId - ID de la cancha
 * @param {Date} startTime - Hora de inicio
 * @param {number} durationMinutes - Duración en minutos
 * @returns {Promise<Object>} - { disponible: boolean, razon: string }
 */
export async function checkAvailability(canchaId, startTime, durationMinutes) {
  const timezone = config.server.timezone || 'America/Mexico_City';
  const endTime = addMinutes(startTime, durationMinutes);
  
  // Convertir startTime de UTC a zona horaria local para verificar horarios
  const startTimeLocal = utcToZonedTime(startTime, timezone);
  
  // Verificar horario del establecimiento
  const horaApertura = parseTime(config.establecimiento.horarioApertura);
  const horaCierre = parseTime(config.establecimiento.horarioCierre);
  const horaInicio = parseTime(format(startTimeLocal, 'HH:mm'));
  
  if (isBefore(horaInicio, horaApertura) || isAfter(horaInicio, horaCierre)) {
    return {
      disponible: false,
      razon: `El horario está fuera del rango de operación (${config.establecimiento.horarioApertura} - ${config.establecimiento.horarioCierre})`,
    };
  }

  // Verificar si hay conflictos con otras reservas
  const reservations = await getReservations(canchaId, startTime, endTime);
  
  for (const reservation of reservations) {
    const reservationStart = new Date(reservation.start.dateTime || reservation.start.date);
    const reservationEnd = new Date(reservation.end.dateTime || reservation.end.date);
    
    // Convertir a zona horaria local para mostrar
    const reservationStartLocal = utcToZonedTime(reservationStart, timezone);
    const reservationEndLocal = utcToZonedTime(reservationEnd, timezone);
    
    // Verificar solapamiento (comparar en UTC)
    if (
      (startTime >= reservationStart && startTime < reservationEnd) ||
      (endTime > reservationStart && endTime <= reservationEnd) ||
      (startTime <= reservationStart && endTime >= reservationEnd)
    ) {
      return {
        disponible: false,
        razon: `La cancha ya está reservada de ${format(reservationStartLocal, 'HH:mm')} a ${format(reservationEndLocal, 'HH:mm')}`,
      };
    }
  }

  return { disponible: true, razon: null };
}

/**
 * Crea una reserva en Google Calendar
 * @param {string} canchaId - ID de la cancha
 * @param {Date} startTime - Hora de inicio
 * @param {number} durationMinutes - Duración en minutos
 * @param {string} clienteNombre - Nombre del cliente
 * @param {string} clienteTelefono - Teléfono del cliente
 * @returns {Promise<Object>} - Evento creado
 */
export async function createReservation(canchaId, startTime, durationMinutes, clienteNombre, clienteTelefono) {
  if (!calendarClient) {
    initializeCalendar();
  }

  const cancha = config.canchas[canchaId];
  if (!cancha) {
    throw new Error(`Cancha ${canchaId} no encontrada`);
  }

  // Verificar disponibilidad antes de crear
  const availability = await checkAvailability(canchaId, startTime, durationMinutes);
  if (!availability.disponible) {
    throw new Error(availability.razon);
  }

  const endTime = addMinutes(startTime, durationMinutes);

  // startTime ya está en UTC (fue convertido en messageController)
  // Solo necesitamos asegurarnos de que endTime también esté en UTC
  const startTimeUTC = startTime;
  const endTimeUTC = endTime;

  const event = {
    summary: `Reserva Padel - ${clienteNombre}`,
    description: `Reserva realizada a través de WhatsApp Bot\nCliente: ${clienteNombre}\nTeléfono: ${clienteTelefono}`,
    start: {
      dateTime: startTimeUTC.toISOString(),
      timeZone: timezone,
    },
    end: {
      dateTime: endTimeUTC.toISOString(),
      timeZone: timezone,
    },
    reminders: {
      useDefault: false,
      overrides: [
        { method: 'email', minutes: 24 * 60 }, // Recordatorio 1 día antes
        { method: 'popup', minutes: 60 }, // Recordatorio 1 hora antes
      ],
    },
  };

  try {
    const response = await calendarClient.events.insert({
      calendarId: cancha.calendarId,
      resource: event,
    });

    console.log(`Reserva creada: ${response.data.id} para ${cancha.nombre}`);
    return response.data;
  } catch (error) {
    console.error('Error creando reserva:', error);
    throw error;
  }
}

/**
 * Obtiene las canchas disponibles en un rango de tiempo
 * @param {Date} startTime - Hora de inicio
 * @param {number} durationMinutes - Duración en minutos
 * @returns {Promise<Array>} - Lista de canchas disponibles
 */
export async function getAvailableCourts(startTime, durationMinutes) {
  const availableCourts = [];

  for (const [canchaId, cancha] of Object.entries(config.canchas)) {
    const availability = await checkAvailability(canchaId, startTime, durationMinutes);
    if (availability.disponible) {
      availableCourts.push({
        id: canchaId,
        nombre: cancha.nombre,
      });
    }
  }

  return availableCourts;
}

/**
 * Obtiene el horario disponible de una cancha en una fecha específica
 * @param {string} canchaId - ID de la cancha
 * @param {Date} date - Fecha a consultar
 * @returns {Promise<Array>} - Lista de horarios disponibles (formato HH:mm)
 */
export async function getAvailableTimeSlots(canchaId, date) {
  const timezone = config.server.timezone || 'America/Mexico_City';
  
  // Crear fechas de inicio y fin del día en la zona horaria local
  const startOfDay = new Date(date);
  startOfDay.setHours(0, 0, 0, 0);
  const endOfDay = new Date(date);
  endOfDay.setHours(23, 59, 59, 999);
  
  // Convertir a UTC para la consulta
  const startOfDayUTC = zonedTimeToUtc(startOfDay, timezone);
  const endOfDayUTC = zonedTimeToUtc(endOfDay, timezone);
  
  const reservations = await getReservations(
    canchaId,
    startOfDayUTC,
    endOfDayUTC
  );

  const horaApertura = parseTime(config.establecimiento.horarioApertura);
  const horaCierre = parseTime(config.establecimiento.horarioCierre);
  const duracion = config.establecimiento.duracionDefault;

  const availableSlots = [];
  let currentTime = new Date(date);
  currentTime.setHours(horaApertura.getHours(), horaApertura.getMinutes(), 0, 0);
  // Convertir a UTC para comparaciones
  let currentTimeUTC = zonedTimeToUtc(currentTime, timezone);

  const endOfDayTime = new Date(date);
  endOfDayTime.setHours(horaCierre.getHours(), horaCierre.getMinutes(), 0, 0);
  const endOfDayTimeUTC = zonedTimeToUtc(endOfDayTime, timezone);
  
  while (currentTimeUTC < endOfDayTimeUTC) {
    const slotEndUTC = addMinutes(currentTimeUTC, duracion);
    
    if (slotEndUTC <= endOfDayTimeUTC) {
      // Verificar si este slot está disponible
      const isAvailable = !reservations.some(reservation => {
        const resStart = new Date(reservation.start.dateTime || reservation.start.date);
        const resEnd = new Date(reservation.end.dateTime || reservation.end.date);
        return (
          (currentTimeUTC >= resStart && currentTimeUTC < resEnd) ||
          (slotEndUTC > resStart && slotEndUTC <= resEnd) ||
          (currentTimeUTC <= resStart && slotEndUTC >= resEnd)
        );
      });

      if (isAvailable) {
        // Convertir de vuelta a zona horaria local para mostrar
        const currentTimeLocal = utcToZonedTime(currentTimeUTC, timezone);
        availableSlots.push(format(currentTimeLocal, 'HH:mm'));
      }
    }

    currentTimeUTC = addMinutes(currentTimeUTC, 30); // Incrementos de 30 minutos
  }

  return availableSlots;
}

/**
 * Parsea una hora en formato HH:mm a un objeto Date
 * @param {string} timeString - Hora en formato HH:mm
 * @returns {Date} - Objeto Date con la hora
 */
function parseTime(timeString) {
  const [hours, minutes] = timeString.split(':').map(Number);
  const date = new Date();
  date.setHours(hours, minutes, 0, 0);
  return date;
}

