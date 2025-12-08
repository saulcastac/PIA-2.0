# Ejemplo de Personalización para Múltiples Establecimientos

Este documento muestra cómo replicar y personalizar el bot para diferentes establecimientos.

## 🏢 Escenario: Múltiples Centros de Padel

Imagina que quieres vender este servicio a 3 centros de padel diferentes:
- Centro A: 2 canchas, horario 9:00-21:00
- Centro B: 4 canchas, horario 8:00-22:00
- Centro C: 3 canchas, horario 10:00-20:00

## 📁 Opción 1: Múltiples Instancias (Recomendado para Producción)

Cada establecimiento tiene su propia instancia del bot.

### Estructura de Directorios

```
padel-bot-service/
├── centro-a/
│   ├── src/
│   ├── .env
│   └── package.json
├── centro-b/
│   ├── src/
│   ├── .env
│   └── package.json
└── centro-c/
    ├── src/
    ├── .env
    └── package.json
```

### Configuración por Centro

**centro-a/.env:**
```env
ESTABLECIMIENTO_NOMBRE=Centro de Padel A
ESTABLECIMIENTO_HORARIO_APERTURA=09:00
ESTABLECIMIENTO_HORARIO_CIERRE=21:00
CANCHA_1_CALENDAR_ID=centroa-cancha1@group.calendar.google.com
CANCHA_2_CALENDAR_ID=centroa-cancha2@group.calendar.google.com
TWILIO_WHATSAPP_NUMBER=whatsapp:+1234567890
PORT=3001
```

**centro-b/.env:**
```env
ESTABLECIMIENTO_NOMBRE=Centro de Padel B
ESTABLECIMIENTO_HORARIO_APERTURA=08:00
ESTABLECIMIENTO_HORARIO_CIERRE=22:00
CANCHA_1_CALENDAR_ID=centrob-cancha1@group.calendar.google.com
CANCHA_2_CALENDAR_ID=centrob-cancha2@group.calendar.google.com
CANCHA_3_CALENDAR_ID=centrob-cancha3@group.calendar.google.com
CANCHA_4_CALENDAR_ID=centrob-cancha4@group.calendar.google.com
TWILIO_WHATSAPP_NUMBER=whatsapp:+1234567891
PORT=3002
```

### Ventajas

- ✅ Aislamiento completo entre establecimientos
- ✅ Fácil de escalar
- ✅ Si un bot falla, los otros siguen funcionando
- ✅ Diferentes versiones/configuraciones por establecimiento

### Desventajas

- ⚠️ Más recursos necesarios
- ⚠️ Más mantenimiento

---

## 📁 Opción 2: Instancia Única Multi-Tenant (Para SaaS)

Un solo servidor maneja múltiples establecimientos.

### Modificaciones Necesarias

1. **Base de datos** para almacenar configuraciones por establecimiento
2. **Identificación del establecimiento** por número de WhatsApp o código
3. **Middleware** para cargar configuración según el establecimiento

### Ejemplo de Estructura

```javascript
// src/models/establecimiento.js
export const establecimientos = {
  'whatsapp:+1234567890': {
    nombre: 'Centro A',
    horarioApertura: '09:00',
    horarioCierre: '21:00',
    canchas: {
      cancha_1: { calendarId: '...' },
      cancha_2: { calendarId: '...' },
    },
  },
  'whatsapp:+1234567891': {
    nombre: 'Centro B',
    // ...
  },
};
```

### Ventajas

- ✅ Un solo servidor para todos
- ✅ Más eficiente en recursos
- ✅ Fácil de actualizar (una vez para todos)

### Desventajas

- ⚠️ Más complejo de implementar
- ⚠️ Si el servidor falla, todos fallan
- ⚠️ Requiere base de datos

---

## 🎨 Personalización del Comportamiento

### Cambiar el Tono del Bot

Edita `src/services/openaiService.js`:

```javascript
const systemPrompt = `Eres un asistente virtual especializado en reservas de canchas de padel.
Tu personalidad es: [AMIGABLE/PROFESIONAL/FORMAL/DIVERTIDA]

INSTRUCCIONES:
- Usa emojis: ✅/❌ (o no uses emojis)
- Tono: [formal/informal]
- ...
`;
```

### Agregar Información Adicional

```javascript
const systemPrompt = `...
INFORMACIÓN ADICIONAL DEL ESTABLECIMIENTO:
- Ubicación: [dirección]
- Teléfono: [teléfono]
- Servicios: [lista de servicios]
- Precios: [información de precios]
...
`;
```

### Personalizar Mensajes de Confirmación

Edita `src/controllers/messageController.js`:

```javascript
return `✅ ¡Reserva confirmada!\n\n` +
       `📅 Fecha: ${fechaFormateada}\n` +
       `🕐 Hora: ${horaFormateada}\n` +
       // Agrega más información personalizada
       `📍 Ubicación: ${config.establecimiento.direccion}\n` +
       `💰 Precio: $${precio}\n` +
       // ...
```

---

## 🔄 Proceso de Replicación Rápida

### Para un Nuevo Establecimiento:

1. **Copia el proyecto**
   ```bash
   cp -r padel-bot centro-nuevo
   cd centro-nuevo
   ```

2. **Configura variables de entorno**
   - Crea `.env` con las credenciales del nuevo establecimiento
   - Configura canchas, horarios, etc.

3. **Crea calendarios en Google Calendar**
   - Un calendario por cancha
   - Obtén los Calendar IDs

4. **Configura Twilio**
   - Crea un nuevo número de WhatsApp (o usa el mismo)
   - Configura el webhook

5. **Obtén refresh token de Google**
   - Usa el script `scripts/getRefreshToken.js`

6. **Inicia el servidor**
   ```bash
   npm install
   npm start
   ```

**Tiempo estimado: 15-30 minutos por establecimiento**

---

## 📊 Comparación de Opciones

| Aspecto | Múltiples Instancias | Multi-Tenant |
|--------|---------------------|--------------|
| Complejidad | Baja | Alta |
| Recursos | Alto | Bajo |
| Escalabilidad | Fácil | Media |
| Mantenimiento | Más trabajo | Menos trabajo |
| Aislamiento | Total | Parcial |
| Recomendado para | < 10 establecimientos | > 10 establecimientos |

---

## 💡 Mejoras Futuras para SaaS

Si planeas vender esto como servicio:

1. **Dashboard Web**
   - Panel de administración por establecimiento
   - Configuración sin tocar código
   - Estadísticas y reportes

2. **Base de Datos**
   - PostgreSQL o MongoDB
   - Almacenar configuraciones, reservas, clientes

3. **Sistema de Pagos**
   - Stripe/PayPal para suscripciones
   - Facturación automática

4. **API REST**
   - Para integraciones externas
   - Webhooks para notificaciones

5. **Multi-idioma**
   - Soporte para diferentes idiomas
   - Configurable por establecimiento

---

## 📝 Checklist de Replicación

Para cada nuevo establecimiento:

- [ ] Copiar proyecto
- [ ] Configurar `.env`
- [ ] Crear calendarios en Google Calendar
- [ ] Obtener Calendar IDs
- [ ] Configurar Twilio (número y webhook)
- [ ] Obtener refresh token de Google
- [ ] Probar con mensajes de prueba
- [ ] Verificar que las reservas se creen correctamente
- [ ] Documentar configuración específica del establecimiento

---

¡Con este sistema puedes replicar el bot para tantos establecimientos como necesites! 🚀

