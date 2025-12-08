import dotenv from 'dotenv';

dotenv.config();

export const config = {
  twilio: {
    accountSid: process.env.TWILIO_ACCOUNT_SID,
    authToken: process.env.TWILIO_AUTH_TOKEN,
    whatsappNumber: process.env.TWILIO_WHATSAPP_NUMBER,
    webhookUrl: process.env.TWILIO_WEBHOOK_URL,
  },
  openai: {
    apiKey: process.env.OPENAI_API_KEY,
    model: process.env.OPENAI_MODEL || 'gpt-4',
  },
  googleCalendar: {
    clientId: process.env.GOOGLE_CALENDAR_CLIENT_ID,
    clientSecret: process.env.GOOGLE_CALENDAR_CLIENT_SECRET,
    redirectUri: process.env.GOOGLE_CALENDAR_REDIRECT_URI,
    refreshToken: process.env.GOOGLE_CALENDAR_REFRESH_TOKEN,
  },
  server: {
    port: process.env.PORT || 3000,
    nodeEnv: process.env.NODE_ENV || 'development',
    timezone: process.env.TIMEZONE || 'America/Mexico_City', // GMT-6
  },
  establecimiento: {
    nombre: process.env.ESTABLECIMIENTO_NOMBRE || 'Centro de Padel',
    horarioApertura: process.env.ESTABLECIMIENTO_HORARIO_APERTURA || '08:00',
    horarioCierre: process.env.ESTABLECIMIENTO_HORARIO_CIERRE || '22:00',
    duracionDefault: parseInt(process.env.DURACION_DEFAULT_MINUTOS) || 60,
  },
  canchas: getCanchasConfig(),
};

function getCanchasConfig() {
  const canchas = {};
  let index = 1;
  
  while (process.env[`CANCHA_${index}_CALENDAR_ID`]) {
    // Permitir nombres personalizados mediante CANCHA_X_NOMBRE
    const nombrePersonalizado = process.env[`CANCHA_${index}_NOMBRE`];
    const nombre = nombrePersonalizado || `Cancha ${index}`;
    
    canchas[`cancha_${index}`] = {
      id: `cancha_${index}`,
      nombre: nombre,
      calendarId: process.env[`CANCHA_${index}_CALENDAR_ID`],
    };
    index++;
  }
  
  // Si no hay canchas configuradas, crear una por defecto
  if (Object.keys(canchas).length === 0) {
    const nombrePersonalizado = process.env.CANCHA_1_NOMBRE;
    canchas.cancha_1 = {
      id: 'cancha_1',
      nombre: nombrePersonalizado || 'Cancha 1',
      calendarId: process.env.CANCHA_1_CALENDAR_ID || '',
    };
  }
  
  return canchas;
}

// Validar configuración crítica
export function validateConfig() {
  const errors = [];
  
  if (!config.twilio.accountSid) errors.push('TWILIO_ACCOUNT_SID es requerido');
  if (!config.twilio.authToken) errors.push('TWILIO_AUTH_TOKEN es requerido');
  if (!config.openai.apiKey) errors.push('OPENAI_API_KEY es requerido');
  if (!config.googleCalendar.clientId) errors.push('GOOGLE_CALENDAR_CLIENT_ID es requerido');
  if (!config.googleCalendar.clientSecret) errors.push('GOOGLE_CALENDAR_CLIENT_SECRET es requerido');
  
  if (errors.length > 0) {
    throw new Error(`Error de configuración:\n${errors.join('\n')}`);
  }
}

