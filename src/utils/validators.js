/**
 * Utilidades de validación
 */

/**
 * Valida que un número de teléfono tenga formato correcto
 * @param {string} phone - Número de teléfono
 * @returns {boolean}
 */
export function isValidPhoneNumber(phone) {
  if (!phone) return false;
  // Formato: whatsapp:+1234567890 o +1234567890
  const phoneRegex = /^(\+?\d{10,15}|whatsapp:\+\d{10,15})$/;
  return phoneRegex.test(phone.replace(/\s+/g, ''));
}

/**
 * Valida que una fecha sea válida y no en el pasado
 * @param {Date} date - Fecha a validar
 * @returns {boolean}
 */
export function isValidFutureDate(date) {
  if (!date || isNaN(date.getTime())) return false;
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  const checkDate = new Date(date);
  checkDate.setHours(0, 0, 0, 0);
  return checkDate >= now;
}

/**
 * Valida que una hora esté en formato correcto
 * @param {string} time - Hora en formato HH:mm
 * @returns {boolean}
 */
export function isValidTime(time) {
  if (!time) return false;
  const timeRegex = /^([0-1][0-9]|2[0-3]):[0-5][0-9]$/;
  return timeRegex.test(time);
}

/**
 * Valida que una duración sea válida (mínimo 30 minutos, máximo 240 minutos)
 * @param {number} duration - Duración en minutos
 * @returns {boolean}
 */
export function isValidDuration(duration) {
  if (!duration || isNaN(duration)) return false;
  return duration >= 30 && duration <= 240;
}

