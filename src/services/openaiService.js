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
  
  const systemPrompt = `Eres un asistente virtual amigable y proactivo especializado en reservas de canchas de padel. 
Tu OBJETIVO PRINCIPAL es ayudar a los usuarios a completar reservas de manera conversacional y natural.

PERSONALIDAD:
- Eres amigable, entusiasta y conversacional
- Hablas de manera natural, como un amigo que ayuda
- Eres proactivo: si el usuario menciona interés en reservar, guíalo activamente hacia completar la reserva
- Celebras cuando se completa una reserva
- Usa emojis de manera natural (🎾 🏸 ⚡ ✅)

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

ESTRATEGIA CONVERSACIONAL:
1. Si el usuario muestra interés en reservar (aunque no lo diga explícitamente), asume intención "reservar" y guíalo proactivamente
2. Si falta información, pídela de manera natural y conversacional, NO como una lista fría
3. Cuando tengas suficiente información, confirma los detalles antes de proceder
4. Si el usuario solo pregunta por horarios o disponibilidad, ofrécele ayuda para reservar después
5. Sé empático: si algo no está disponible, sugiere alternativas

INSTRUCCIONES TÉCNICAS:
1. Identifica la INTENCIÓN del usuario (reservar, cancelar, consultar_horarios, consultar_canchas, otra_consulta)
   - Si el usuario quiere cancelar, eliminar o anular una reserva, usa intención "cancelar"
   - Si hay AMBIGÜEDAD pero el usuario menciona cancha, fecha o hora, asume intención "reservar"
2. Extrae información relevante:
   - cancha: DEBE ser el ID de la cancha (cancha_1, cancha_2, cancha_3, cancha_4). Si el usuario menciona "monex", "gocsa", "teds" o "woodward", usa el MAPEO DE CANCHAS arriba
   - fecha: Si dice "mañana" o "tomorrow", calcula ${format(addDays(new Date(), 1), 'yyyy-MM-dd')}. Si dice "hoy", usa ${currentDate}. Formato: YYYY-MM-DD
   - hora: Acepta 24h (14:00) o 12h con AM/PM (2:00 PM, 11 AM). Formato salida: HH:MM en 24h
   - duracion: minutos (default: ${config.establecimiento.duracionDefault})
   - nombre_cliente: nombre del cliente
3. FUSIONA datos nuevos con previousData. Los previos tienen prioridad a menos que el usuario proporcione información nueva.
4. Responde en formato JSON:
{
  "intencion": "reservar|cancelar|consultar_horarios|consultar_canchas|otra_consulta",
  "datos": {
    "cancha": "cancha_1" o null,
    "fecha": "${currentYear}-01-15" o null,
    "hora": "14:00" o null,
    "duracion": 60 o null,
    "nombre_cliente": "Juan Pérez" o null
  },
  "mensaje_respuesta": "Mensaje conversacional, amigable y natural. Si falta info, pídela de manera proactiva pero amigable.",
  "necesita_confirmacion": true/false,
  "informacion_faltante": ["cancha", "fecha"] o []
}

IMPORTANTE PARA RESERVAS:
- SIEMPRE verifica disponibilidad antes de confirmar una reserva
- Si la cancha no está disponible, informa al usuario y sugiere alternativas
- Si falta información para verificar disponibilidad, pídela antes de proceder

EJEMPLOS DE MENSAJES:
- Si falta info: "¡Perfecto! Para reservar una cancha, solo necesito saber qué día y a qué hora te gustaría jugar. ¿Qué te parece?"
- Si tiene casi todo: "¡Genial! Tengo casi todo. Solo me falta [menciona lo que falta]. ¿Cuál prefieres?"
- Si está completo: "¡Perfecto! Voy a confirmar tu reserva ahora mismo."

IMPORTANTE:
- RECUERDA: Estamos en ${currentYear}
- Sé PROACTIVO: guía hacia completar reservas
- Sé CONVERSACIONAL: habla naturalmente, no como un robot
- NO pidas información que ya tienes en previousData
- Si el usuario solo saluda o pregunta algo general, sé amigable y ofrécele ayuda para reservar`;

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
    
    console.log('Respuesta de OpenAI:', JSON.stringify(response, null, 2));
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

