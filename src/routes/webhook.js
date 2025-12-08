import express from 'express';
import { handleIncomingMessage } from '../controllers/messageController.js';

const router = express.Router();

/**
 * Webhook para recibir mensajes de Twilio
 * POST /webhook
 */
router.post('/', async (req, res) => {
  try {
    const { From, Body } = req.body;

    if (!From || !Body) {
      return res.status(400).send('Missing required fields');
    }

    // Responder inmediatamente a Twilio (requerido)
    res.status(200).send('OK');

    // Procesar mensaje de forma asíncrona
    handleIncomingMessage(From, Body).catch(error => {
      console.error('Error procesando mensaje en webhook:', error);
    });
  } catch (error) {
    console.error('Error en webhook:', error);
    res.status(500).send('Internal Server Error');
  }
});

/**
 * Endpoint para verificar el estado del webhook (usado por Twilio)
 * GET /webhook
 */
router.get('/', (req, res) => {
  res.status(200).send('Webhook activo');
});

export default router;

