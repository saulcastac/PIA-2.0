/**
 * Sistema de memoria de conversación para recordar información entre mensajes
 * Almacena información por número de teléfono
 */

// Almacenamiento en memoria (en producción podrías usar Redis o una base de datos)
const conversations = new Map();

// Tiempo de expiración: 30 minutos de inactividad
const EXPIRATION_TIME = 30 * 60 * 1000; // 30 minutos en milisegundos

/**
 * Obtiene o crea una conversación para un número de teléfono
 * @param {string} phoneNumber - Número de teléfono
 * @returns {Object} - Estado de la conversación
 */
export function getConversation(phoneNumber) {
  const normalizedPhone = normalizePhone(phoneNumber);
  
  if (!conversations.has(normalizedPhone)) {
    conversations.set(normalizedPhone, {
      phoneNumber: normalizedPhone,
      datos: {},
      lastActivity: Date.now(),
      messageHistory: [],
    });
  }
  
  const conversation = conversations.get(normalizedPhone);
  conversation.lastActivity = Date.now();
  
  return conversation;
}

/**
 * Actualiza los datos de una conversación
 * @param {string} phoneNumber - Número de teléfono
 * @param {Object} newData - Nuevos datos a agregar/actualizar
 */
export function updateConversationData(phoneNumber, newData) {
  const conversation = getConversation(phoneNumber);
  
  // Fusionar datos nuevos con los existentes (los nuevos tienen prioridad)
  conversation.datos = {
    ...conversation.datos,
    ...newData,
  };
  
  // Limpiar datos si se completa una reserva
  if (newData.reserva_completada) {
    conversation.datos = {};
    conversation.messageHistory = [];
  }
}

/**
 * Agrega un mensaje al historial de la conversación
 * @param {string} phoneNumber - Número de teléfono
 * @param {string} role - 'user' o 'assistant'
 * @param {string} content - Contenido del mensaje
 */
export function addMessageToHistory(phoneNumber, role, content) {
  const conversation = getConversation(phoneNumber);
  
  conversation.messageHistory.push({
    role,
    content,
    timestamp: Date.now(),
  });
  
  // Mantener solo los últimos 10 mensajes para no sobrecargar el contexto
  if (conversation.messageHistory.length > 10) {
    conversation.messageHistory = conversation.messageHistory.slice(-10);
  }
}

/**
 * Obtiene el historial de mensajes de una conversación
 * @param {string} phoneNumber - Número de teléfono
 * @returns {Array} - Historial de mensajes
 */
export function getMessageHistory(phoneNumber) {
  const conversation = getConversation(phoneNumber);
  return conversation.messageHistory;
}

/**
 * Obtiene los datos acumulados de una conversación
 * @param {string} phoneNumber - Número de teléfono
 * @returns {Object} - Datos de la conversación
 */
export function getConversationData(phoneNumber) {
  const conversation = getConversation(phoneNumber);
  return conversation.datos;
}

/**
 * Limpia conversaciones expiradas
 */
export function cleanExpiredConversations() {
  const now = Date.now();
  
  for (const [phone, conversation] of conversations.entries()) {
    if (now - conversation.lastActivity > EXPIRATION_TIME) {
      conversations.delete(phone);
    }
  }
}

/**
 * Normaliza un número de teléfono para usar como clave
 * @param {string} phoneNumber - Número de teléfono
 * @returns {string} - Número normalizado
 */
function normalizePhone(phoneNumber) {
  // Remover prefijo whatsapp: y normalizar
  return phoneNumber.replace(/^whatsapp:/i, '').trim();
}

// Limpiar conversaciones expiradas cada 5 minutos
setInterval(cleanExpiredConversations, 5 * 60 * 1000);


