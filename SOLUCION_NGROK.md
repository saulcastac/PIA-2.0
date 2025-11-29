# Solución al Error 502 Bad Gateway en ngrok

## 🔴 Problema

El error **502 Bad Gateway** en ngrok significa que ngrok recibió el request pero **no pudo conectarse** al servidor Flask en `localhost:5000`.

El mensaje de error indica:
```
dial tcp [::1]:5000: connectex: No se puede establecer una conexión 
ya que el equipo de destino denegó expresamente dicha conexión.
```

## ✅ Solución Paso a Paso

### 1. Verificar que el servidor Flask esté corriendo

**IMPORTANTE**: El servidor Flask debe estar corriendo **ANTES** de iniciar ngrok.

1. Abre una terminal/PowerShell
2. Navega a la carpeta del proyecto:
   ```bash
   cd "C:\Users\saulc\Documents\Cursor code\PAD-IA"
   ```
3. Ejecuta el servidor:
   ```bash
   python main.py
   ```
4. **Espera** a ver estos mensajes en la consola:
   ```
   ================================================================================
   INICIANDO SERVIDOR FLASK
   Host: 0.0.0.0
   Puerto: 5000
   ================================================================================
   ✅ Servidor Flask verificado y corriendo correctamente
   ✅ Sistema iniciado correctamente
   ```
5. **NO CIERRES** esta terminal. El servidor debe seguir corriendo.

### 2. Verificar que el servidor esté funcionando

En **otra terminal nueva**, ejecuta el script de verificación:

```bash
python verificar_servidor.py
```

Deberías ver:
```
✅ Servidor Flask está corriendo correctamente
✅ Endpoint /webhook está disponible
✅ TODO ESTÁ FUNCIONANDO CORRECTAMENTE
```

Si ves errores, el servidor no está corriendo correctamente. Vuelve al paso 1.

### 3. Iniciar ngrok

**Solo después** de que el servidor Flask esté corriendo:

1. Abre **otra terminal nueva** (deja el servidor Flask corriendo)
2. Inicia ngrok:
   ```bash
   ngrok http 5000
   ```
   O si usas el script:
   ```powershell
   .\start_ngrok.ps1
   ```

3. Deberías ver algo como:
   ```
   Forwarding   https://xxxx-xx-xx-xx-xx.ngrok-free.app -> http://localhost:5000
   ```

### 4. Configurar el webhook en Twilio

1. Copia la URL de ngrok (la que termina en `.ngrok-free.app`)
2. Ve a la consola de Twilio
3. Configura el webhook a: `https://tu-url-ngrok.ngrok-free.app/webhook`

### 5. Probar el webhook

Envía un mensaje de WhatsApp al bot. Deberías ver:
- En ngrok: Un request `POST /webhook` con código `200 OK`
- En la consola del servidor: Los logs del mensaje recibido

## 🔧 Solución de Problemas

### Error: "El servidor no está corriendo"

**Causa**: El servidor Flask no se inició o se cerró.

**Solución**:
1. Verifica que `python main.py` esté corriendo
2. Verifica que veas el mensaje "✅ Servidor Flask verificado"
3. Si el servidor se cierra inmediatamente, revisa los logs de error

### Error: "Puerto 5000 ya está en uso"

**Causa**: Otro proceso está usando el puerto 5000.

**Solución**:
1. En Windows, busca qué proceso usa el puerto:
   ```powershell
   netstat -ano | findstr :5000
   ```
2. Termina el proceso o cambia el puerto en `whatsapp_bot_twilio.py` (línea 259)

### Error: "Firewall bloqueando conexión"

**Causa**: El firewall de Windows está bloqueando el puerto 5000.

**Solución**:
1. Abre el Firewall de Windows
2. Permite Python o el puerto 5000
3. O desactiva temporalmente el firewall para probar

### El servidor se cierra inmediatamente

**Causa**: Error al iniciar el servidor o problema con las dependencias.

**Solución**:
1. Revisa los logs de error en la consola
2. Verifica que todas las dependencias estén instaladas:
   ```bash
   pip install -r requirements.txt
   ```
3. Verifica que el archivo `.env` esté configurado correctamente

## 📋 Checklist

Antes de usar ngrok, verifica:

- [ ] El servidor Flask está corriendo (`python main.py`)
- [ ] Ves el mensaje "✅ Servidor Flask verificado"
- [ ] El script `verificar_servidor.py` muestra "✅ TODO ESTÁ FUNCIONANDO"
- [ ] ngrok está corriendo y muestra la URL de forwarding
- [ ] El webhook de Twilio está configurado con la URL de ngrok

## 🚀 Orden Correcto de Ejecución

1. **Primero**: Iniciar el servidor Flask (`python main.py`)
2. **Segundo**: Verificar que el servidor esté corriendo (`python verificar_servidor.py`)
3. **Tercero**: Iniciar ngrok (`ngrok http 5000`)
4. **Cuarto**: Configurar el webhook en Twilio con la URL de ngrok
5. **Quinto**: Probar enviando un mensaje de WhatsApp

## 💡 Tips

- **Mantén ambas terminales abiertas**: Una para el servidor Flask y otra para ngrok
- **Si cambias algo en el código**: Reinicia el servidor Flask (Ctrl+C y vuelve a ejecutar)
- **Si ngrok se desconecta**: Reinicia ngrok y actualiza la URL del webhook en Twilio
- **Para desarrollo**: Usa ngrok con authtoken para evitar límites de tiempo








