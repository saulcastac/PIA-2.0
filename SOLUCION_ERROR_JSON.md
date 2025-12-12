# Solución para Error "Unexpected end of JSON input" en Railway

## Problema
El error `SyntaxError: Unexpected end of JSON input` ocurre cuando OpenAI devuelve una respuesta que no es JSON válido o está incompleta.

## Solución

### 1. Usar `response_format: { type: "json_object" }`

**CRÍTICO**: Siempre incluir esto en la llamada a OpenAI:

```javascript
const response = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [...],
    response_format: { type: "json_object" }  // ← ESTO ES CRÍTICO
});
```

### 2. Limpiar la respuesta antes de parsear

```javascript
let aiResponse = response.choices[0]?.message?.content?.trim();

// Remover markdown si existe
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
```

### 3. Manejo robusto de errores

```javascript
try {
    parsedResponse = JSON.parse(aiResponse);
} catch (parseError) {
    console.error("Error parseando JSON:", parseError);
    console.error("Respuesta recibida:", aiResponse);
    
    // Intentar extraer JSON si está embebido
    const jsonMatch = aiResponse.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
        parsedResponse = JSON.parse(jsonMatch[0]);
    } else {
        throw new Error(`Respuesta no es JSON válido`);
    }
}
```

### 4. Validar respuesta antes de parsear

```javascript
if (!aiResponse) {
    throw new Error("Respuesta vacía de OpenAI");
}

if (!aiResponse.trim()) {
    throw new Error("Respuesta vacía después de limpiar");
}
```

### 5. Retornar fallback en lugar de lanzar error

En lugar de dejar que el error se propague, retorna un objeto de fallback:

```javascript
catch (error) {
    console.error("Error procesando mensaje con OpenAI:", error);
    
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
```

## Archivo de ejemplo

Ver `openaiService.example.js` para la implementación completa.

## Verificación

Después de aplicar estos cambios:

1. Verifica que `response_format: { type: "json_object" }` esté presente
2. Agrega logging para ver la respuesta cruda de OpenAI
3. Prueba con diferentes mensajes
4. Verifica que los errores se manejen gracefully

## Notas adicionales

- El modelo `gpt-4o-mini` es más confiable que `gpt-3.5-turbo` para JSON
- `temperature: 0.1` ayuda a obtener respuestas más consistentes
- Siempre valida que la respuesta no esté vacía antes de parsear

