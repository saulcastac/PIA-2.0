import OpenAI from 'openai';
import { config } from '../config/config.js';

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
 * @returns {Promise<Object>} - Respuesta estructurada con intención y datos extraídos
 */
export async function processMessageWithAI(userMessage, context = {}) {
  const systemPrompt = `Eres un asistente virtual especializado en reservas de canchas de padel. 
Tu tarea es entender las solicitudes de los usuarios y extraer información relevante.

INFORMACIÓN DEL ESTABLECIMIENTO:
- Nombre: ${config.establecimiento.nombre}
- Horario: ${config.establecimiento.horarioApertura} - ${config.establecimiento.horarioCierre}
- Duración por defecto: ${config.establecimiento.duracionDefault} minutos

CANCHAS DISPONIBLES:
${Object.values(config.canchas).map(c => `- ${c.nombre} (ID: ${c.id})`).join('\n')}

${context.canchasDisponibles ? `\nCANCHAS DISPONIBLES EN ESTE MOMENTO:\n${context.canchasDisponibles}` : ''}

INSTRUCCIONES:
1. Identifica la INTENCIÓN del usuario (reservar, consultar_horarios, consultar_canchas, otra_consulta)
2. Extrae información relevante:
   - cancha: número o nombre de la cancha (si se menciona)
   - fecha: fecha de la reserva (si se menciona, usar formato YYYY-MM-DD)
   - hora: hora de inicio (formato HH:MM en 24 horas)
   - duracion: duración en minutos (default: ${config.establecimiento.duracionDefault})
   - nombre_cliente: nombre del cliente (si se menciona)
3. Si la intención es "reservar", asegúrate de extraer: cancha, fecha, hora
4. Responde en formato JSON con esta estructura:
{
  "intencion": "reservar|consultar_horarios|consultar_canchas|otra_consulta",
  "datos": {
    "cancha": "cancha_1" o null,
    "fecha": "2024-01-15" o null,
    "hora": "14:00" o null,
    "duracion": 60 o null,
    "nombre_cliente": "Juan Pérez" o null
  },
  "mensaje_respuesta": "Mensaje amigable para el usuario",
  "necesita_confirmacion": true/false,
  "informacion_faltante": ["cancha", "fecha"] o []
}

IMPORTANTE:
- Si falta información crítica para una reserva, indica qué falta en "informacion_faltante"
- Si el usuario pregunta sobre horarios o disponibilidad, usa intención "consultar_horarios" o "consultar_canchas"
- Sé amigable y profesional en "mensaje_respuesta"
- Si no entiendes algo, pregunta amablemente`;

  try {
    const client = getOpenAIClient();
    const completion = await client.chat.completions.create({
      model: config.openai.model,
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userMessage },
      ],
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

