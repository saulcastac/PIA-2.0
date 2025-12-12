/**
 * Servicio de OpenAI mejorado para evitar errores de parsing JSON
 * Solución para el error: "Unexpected end of JSON input"
 */

async function processMessageWithAI(message, context = {}) {
    try {
        const OpenAI = require('openai');
        const openai = new OpenAI({
            apiKey: process.env.OPENAI_API_KEY
        });

        // Construir contexto para el prompt
        const contextStr = context ? Object.entries(context)
            .filter(([_, v]) => v)
            .map(([k, v]) => `${k}: ${v}`)
            .join(', ') : '';

        const today = new Date();
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);
        const tomorrowStr = tomorrow.toISOString().split('T')[0];

        const prompt = `Eres un asistente amigable para reservas de canchas de pádel.

Mensaje del usuario: "${message}"
${contextStr ? `Contexto: ${contextStr}` : ''}

FECHA ACTUAL: ${today.toISOString().split('T')[0]}
FECHA MAÑANA: ${tomorrowStr}

Extrae información de reserva en formato JSON estricto:
{
  "es_reserva": true,
  "nombre": string | null,
  "cancha": "MONEX" | "GOCSA" | "WOODWARD" | "TEDS" | null,
  "fecha": "YYYY-MM-DD",
  "hora": "HH:MM",
  "duracion": 60,
  "confirmado": boolean
}

REGLAS:
- Canchas: MONEX, GOCSA, WOODWARD, TEDS (siempre mayúsculas)
- Fecha formato: YYYY-MM-DD
- Hora formato: HH:MM (24h)
- Si no hay fecha, usa mañana: ${tomorrowStr}

Responde SOLO con JSON válido, sin texto adicional.`;

        // Llamada a OpenAI con formato JSON forzado
        const response = await openai.chat.completions.create({
            model: "gpt-4o-mini",
            messages: [
                {
                    role: "system",
                    content: `Eres un asistente para reservas de pádel. 
                    Siempre respondes SOLO con JSON válido, sin texto adicional.
                    Formato: fechas YYYY-MM-DD, horas HH:MM (24h), canchas en mayúsculas.`
                },
                {
                    role: "user",
                    content: prompt
                }
            ],
            max_tokens: 400,
            temperature: 0.1,
            response_format: { type: "json_object" }  // CRÍTICO: Fuerza formato JSON
        });

        // Extraer respuesta
        let aiResponse = response.choices[0]?.message?.content?.trim();
        
        if (!aiResponse) {
            throw new Error("Respuesta vacía de OpenAI");
        }

        // Limpiar respuesta si tiene markdown o texto adicional
        aiResponse = aiResponse.trim();
        
        // Remover bloques de código markdown si existen
        if (aiResponse.startsWith('```json')) {
            aiResponse = aiResponse.slice(7);
        }
        if (aiResponse.startsWith('```')) {
            aiResponse = aiResponse.slice(3);
        }
        if (aiResponse.endsWith('```')) {
            aiResponse = aiResponse.slice(0, -3);
        }
        aiResponse = aiResponse.trim();

        // Validar que no esté vacío después de limpiar
        if (!aiResponse) {
            throw new Error("Respuesta vacía después de limpiar");
        }

        // Intentar parsear JSON con manejo de errores mejorado
        let parsedResponse;
        try {
            parsedResponse = JSON.parse(aiResponse);
        } catch (parseError) {
            // Log del error para debugging
            console.error("Error parseando JSON:", parseError);
            console.error("Respuesta recibida:", aiResponse);
            console.error("Longitud de respuesta:", aiResponse.length);
            
            // Intentar extraer JSON si está embebido en texto
            const jsonMatch = aiResponse.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
                try {
                    parsedResponse = JSON.parse(jsonMatch[0]);
                    console.log("JSON extraído exitosamente del texto");
                } catch (e) {
                    throw new Error(`Error parseando JSON extraído: ${e.message}`);
                }
            } else {
                throw new Error(`Respuesta no es JSON válido: ${aiResponse.substring(0, 100)}...`);
            }
        }

        // Validar estructura básica
        if (typeof parsedResponse !== 'object' || parsedResponse === null) {
            throw new Error("Respuesta parseada no es un objeto");
        }

        return parsedResponse;

    } catch (error) {
        console.error("Error procesando mensaje con OpenAI:", error);
        
        // Retornar respuesta de fallback en lugar de lanzar error
        return {
            es_reserva: true,
            nombre: null,
            cancha: null,
            fecha: null,
            hora: null,
            duracion: 60,
            confirmado: false,
            error: error.message
        };
    }
}

module.exports = {
    processMessageWithAI
};

