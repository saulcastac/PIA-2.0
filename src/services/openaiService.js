import OpenAI from 'openai';
import { config } from '../config/config.js';
import { addDays, format } from 'date-fns';

// Inicializar cliente de OpenAI de forma lazy
let openai = null;

function getOpenAIClient() {
  if (!openai) {
    const apiKey = config.openai.apiKey || process.env.OPENAI_API_KEY;
    
    if (!apiKey) {
      throw new Error('OPENAI_API_KEY no está configurada. Por favor, configura la variable de entorno OPENAI_API_KEY.');
    }
    
    openai = new OpenAI({
      apiKey: apiKey,
    });
  }
  
  return openai;
}

/**
 * Procesa un mensaje del usuario usando ChatGPT para entender la intención
 * y extraer información relevante sobre reservas
 * @param {string} userMessage - Mensaje del usuario
 * @param {Object} context - Contexto adicional (canchas disponibles, horarios, etc.)
 * @param {Array} messageHistory - Historial de mensajes previos de la conversación
 * @param {Object} previousData - Datos previos de la conversación
 * @returns {Promise<Object>} - Respuesta estructurada con intención y datos extraídos
 */
export async function processMessageWithAI(userMessage, context = {}, messageHistory = [], previousData = {}) {
  const now = new Date();
  const currentYear = now.getFullYear();
  const currentDate = now.toISOString().split('T')[0]; // YYYY-MM-DD
  
  // Mapeo de nombres de canchas para reconocimiento
  const canchasMap = Object.values(config.canchas).map(c => {
    return `- "${c.nombre}" (ID: ${c.id})`;
  }).join('\n');
  
  // Mapeo específico de nombres alternativos a IDs
  const nombresAlternativos = ['monex', 'gocsa', 'teds', 'woodward'];
  const canchasMapping = Object.entries(config.canchas)
    .map(([id, cancha], index) => {
      const nombreAlt = nombresAlternativos[index] || '';
      if (nombreAlt) {
        return `- "${nombreAlt}" o "${cancha.nombre}" → ${id}`;
      }
      return `- "${cancha.nombre}" → ${id}`;
    })
    .join('\n');
  
  const systemPrompt = `Eres un asistente virtual especializado en reservas de canchas de padel. 
Tu tarea es entender las solicitudes de los usuarios y extraer información relevante.

FECHA ACTUAL: ${currentDate} (Año ${currentYear})
IMPORTANTE: Estamos en ${currentYear}, NO en 2023 o 2024. Las fechas deben ser para ${currentYear} o ${currentYear + 1}.

INFORMACIÓN DEL ESTABLECIMIENTO:
- Nombre: ${config.establecimiento.nombre}
- Horario: ${config.establecimiento.horarioApertura} - ${config.establecimiento.horarioCierre}
- Duración por defecto: ${config.establecimiento.duracionDefault} minutos

CANCHAS DISPONIBLES:
${canchasMap}

${canchasMapping}

${context.canchasDisponibles ? `\nCANCHAS DISPONIBLES EN ESTE MOMENTO:\n${context.canchasDisponibles}` : ''}

${Object.keys(previousData).length > 0 ? `\nINFORMACIÓN PREVIA DE ESTA CONVERSACIÓN:\n${JSON.stringify(previousData, null, 2)}\n\nIMPORTANTE: Usa esta información previa para completar los datos faltantes. Si el usuario ya proporcionó información (como cancha, fecha, hora, nombre), CONSÉRVALA y no la pidas de nuevo a menos que el usuario quiera cambiarla.` : ''}

INSTRUCCIONES:
1. Identifica la INTENCIÓN del usuario (reservar, consultar_horarios, consultar_canchas, otra_consulta)
2. Extrae información relevante:
   - cancha: DEBE ser el ID de la cancha (cancha_1, cancha_2, cancha_3, cancha_4). Si el usuario menciona "monex", "gocsa", "teds" o "woodward", o el nombre de la cancha, usa el MAPEO DE CANCHAS arriba para convertir al ID correcto
   - fecha: fecha de la reserva. Si el usuario dice "mañana" o "tomorrow", calcula la fecha de mañana (${format(addDays(new Date(), 1), 'yyyy-MM-dd')}). Si dice "hoy" o "today", usa ${currentDate}. Si menciona un día de la semana, calcula la fecha correspondiente. Formato de salida: YYYY-MM-DD para ${currentYear} o ${currentYear + 1}
   - hora: hora de inicio. Acepta formato 24 horas (14:00) o 12 horas con AM/PM (2:00 PM, 11 AM, 11am). Formato de salida: HH:MM en 24 horas (ej: "11:00" para 11 AM, "14:00" para 2 PM, "23:00" para 11 PM)
   - duracion: duración en minutos (default: ${config.establecimiento.duracionDefault})
   - nombre_cliente: nombre del cliente (si se menciona)
3. Si la intención es "reservar", asegúrate de extraer: cancha, fecha, hora
4. FUSIONA los datos nuevos con los datos previos (previousData). Los datos previos tienen prioridad a menos que el usuario proporcione información nueva que los reemplace.
5. Responde en formato JSON con esta estructura:
{
  "intencion": "reservar|consultar_horarios|consultar_canchas|otra_consulta",
  "datos": {
    "cancha": "cancha_1" o null (debe ser el ID, no el nombre),
    "fecha": "${currentYear}-01-15" o null (formato YYYY-MM-DD, año ${currentYear} o ${currentYear + 1}),
    "hora": "14:00" o null,
    "duracion": 60 o null,
    "nombre_cliente": "Juan Pérez" o null
  },
  "mensaje_respuesta": "Mensaje amigable para el usuario",
  "necesita_confirmacion": true/false,
  "informacion_faltante": ["cancha", "fecha"] o []
}

IMPORTANTE:
- RECUERDA: Estamos en ${currentYear}, las fechas deben ser para ${currentYear} o ${currentYear + 1}
- Si falta información crítica para una reserva, indica qué falta en "informacion_faltante"
- Si el usuario pregunta sobre horarios o disponibilidad, usa intención "consultar_horarios" o "consultar_canchas"
- Sé amigable y profesional en "mensaje_respuesta"
- Si no entiendes algo, pregunta amablemente
- NO pidas información que ya tienes en previousData a menos que el usuario quiera cambiarla`;

  try {
    const client = getOpenAIClient();
    
    // Construir array de mensajes con historial
    const messages = [
      { role: 'system', content: systemPrompt },
    ];
    
    // Agregar historial de mensajes previos (últimos 5 para no sobrecargar)
    const recentHistory = messageHistory.slice(-5);
    messages.push(...recentHistory);
    
    // Agregar mensaje actual
    messages.push({ role: 'user', content: userMessage });
    
    const completion = await client.chat.completions.create({
      model: config.openai.model,
      messages: messages,
      temperature: 0.3,
      response_format: { type: 'json_object' },
    });

    const response = JSON.parse(completion.choices[0].message.content);
    
    console.log('Respuesta de OpenAI:', response);
    return response;
  } catch (error) {
    console.error('Error procesando mensaje con OpenAI:', error);
    
    // Respuesta de fallback
    return {
      intencion: 'otra_consulta',
      datos: {},
      mensaje_respuesta: 'Lo siento, hubo un error procesando tu mensaje. Por favor, intenta de nuevo o contacta directamente con el establecimiento.',
      necesita_confirmacion: false,
      informacion_faltante: [],
    };
  }
}

/**
 * Genera una respuesta amigable para el usuario basada en el contexto
 * @param {string} intent - Intención detectada
 * @param {Object} data - Datos extraídos
 * @param {Object} context - Contexto adicional
 * @returns {Promise<string>} - Mensaje de respuesta
 */
export async function generateResponse(intent, data, context = {}) {
  const userMessage = `Intención: ${intent}. Datos: ${JSON.stringify(data)}. Contexto: ${JSON.stringify(context)}. 
Genera una respuesta amigable y profesional en español para el usuario.`;

  try {
    const client = getOpenAIClient();
    const completion = await client.chat.completions.create({
      model: config.openai.model,
      messages: [
        {
          role: 'system',
          content: 'Eres un asistente virtual amigable y profesional para un centro de padel. Responde siempre en español de manera clara y concisa.',
        },
        { role: 'user', content: userMessage },
      ],
      temperature: 0.7,
      max_tokens: 200,
    });

    return completion.choices[0].message.content.trim();
  } catch (error) {
    console.error('Error generando respuesta:', error);
    return 'Gracias por tu mensaje. Estamos procesando tu solicitud.';
  }
}

