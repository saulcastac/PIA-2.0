import twilio from 'twilio';
import { config } from '../config/config.js';

// Inicializar cliente de Twilio de forma lazy
let client = null;

function getTwilioClient() {
  if (!client) {
    const accountSid = config.twilio.accountSid || process.env.TWILIO_ACCOUNT_SID;
    const authToken = config.twilio.authToken || process.env.TWILIO_AUTH_TOKEN;
    
    if (!accountSid || !authToken) {
      throw new Error('TWILIO_ACCOUNT_SID y TWILIO_AUTH_TOKEN son requeridos. Por favor, configura estas variables de entorno.');
    }
    
    client = twilio(accountSid, authToken);
  }
  
  return client;
}

/**
 * Envía un mensaje de WhatsApp a través de Twilio
 * @param {string} to - Número de teléfono destino (formato: whatsapp:+1234567890)
 * @param {string} message - Mensaje a enviar
 * @returns {Promise<Object>} - Respuesta de Twilio
 */
export async function sendWhatsAppMessage(to, message) {
  try {
    const twilioClient = getTwilioClient();
    const response = await twilioClient.messages.create({
      from: config.twilio.whatsappNumber,
      to: to,
      body: message,
    });
    
    console.log(`Mensaje enviado a ${to}: ${response.sid}`);
    return response;
  } catch (error) {
    console.error('Error enviando mensaje de WhatsApp:', error);
    throw error;
  }
}

/**
 * Valida que un número de teléfono tenga el formato correcto para WhatsApp
 * @param {string} phoneNumber - Número de teléfono
 * @returns {string} - Número formateado
 */
export function formatPhoneNumber(phoneNumber) {
  // Remover espacios y caracteres especiales
  let cleaned = phoneNumber.replace(/\s+/g, '').replace(/[^\d+]/g, '');
  
  // Si no empieza con whatsapp:, agregarlo
  if (!cleaned.startsWith('whatsapp:')) {
    // Si no empieza con +, agregarlo
    if (!cleaned.startsWith('+')) {
      cleaned = '+' + cleaned;
    }
    cleaned = 'whatsapp:' + cleaned;
  }
  
  return cleaned;
}

/**
 * Extrae el número de teléfono del formato de Twilio
 * @param {string} twilioNumber - Número en formato Twilio (whatsapp:+1234567890)
 * @returns {string} - Número limpio
 */
export function extractPhoneNumber(twilioNumber) {
  return twilioNumber.replace('whatsapp:', '');
}

