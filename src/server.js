import express from 'express';
import { config, validateConfig } from './config/config.js';
import { initializeCalendar } from './services/calendarService.js';
import webhookRouter from './routes/webhook.js';

const app = express();

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Validar configuración al iniciar
try {
  validateConfig();
  console.log('✅ Configuración validada correctamente');
} catch (error) {
  console.error('❌ Error de configuración:', error.message);
  process.exit(1);
}

// Inicializar Google Calendar
try {
  initializeCalendar();
  console.log('✅ Google Calendar inicializado');
} catch (error) {
  console.error('⚠️ Error inicializando Google Calendar:', error.message);
  console.log('⚠️ Continuando sin Google Calendar (algunas funciones pueden no estar disponibles)');
}

// Rutas
app.use('/webhook', webhookRouter);

// Ruta de salud
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    service: 'Padel Booking Bot',
    version: '2.0.0',
  });
});

// Ruta raíz
app.get('/', (req, res) => {
  res.json({
    message: 'Bot de WhatsApp para reservas de canchas de padel',
    version: '2.0.0',
    endpoints: {
      webhook: '/webhook',
      health: '/health',
    },
  });
});

// Manejo de errores
app.use((err, req, res, next) => {
  console.error('Error no manejado:', err);
  res.status(500).json({
    error: 'Internal Server Error',
    message: err.message,
  });
});

// Iniciar servidor
const PORT = config.server.port;
app.listen(PORT, () => {
  console.log(`🚀 Servidor iniciado en puerto ${PORT}`);
  console.log(`📱 Webhook URL: http://localhost:${PORT}/webhook`);
  console.log(`🏸 Establecimiento: ${config.establecimiento.nombre}`);
  console.log(`⏰ Horario: ${config.establecimiento.horarioApertura} - ${config.establecimiento.horarioCierre}`);
  console.log(`🏟️ Canchas configuradas: ${Object.keys(config.canchas).length}`);
});

