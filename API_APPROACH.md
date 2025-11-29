# Nuevo Enfoque API para Playtomic

## Resumen de Cambios

El proyecto ha sido reestructurado para usar **llamadas directas a la API de Playtomic** en lugar de automatización HTML/Selenium. Este enfoque es más eficiente, confiable y rápido.

## Estructura de la API de Playtomic

### URL Base de Pagos
```
https://playtomic.com/api/web-app/payments
```

### Parámetros de Reserva
- `type=CUSTOMER_MATCH` - Tipo de operación para clientes registrados
- `tenant_id` - ID del club/organización
- `resource_id` - ID de la cancha específica
- `start` - Fecha y hora en formato ISO 8601 UTC
- `duration` - Duración en minutos (típicamente 60)

### Ejemplo de URL
```
https://playtomic.com/api/web-app/payments?type=CUSTOMER_MATCH&tenant_id=65a5b336-e05c-4989-a3b8-3374e9ad335f&resource_id=da1fda51-61f8-4432-92b9-d93f980ed106&start=2025-11-27T19%3A30%3A00.000Z&duration=60
```

## Archivos Principales

### 1. `playtomic_api_client.py`
- Cliente HTTP para interactuar con la API de Playtomic
- Maneja autenticación, reservas y consulta de disponibilidad
- Usa `aiohttp` para peticiones HTTP asíncronas

### 2. `playtomic_automation.py` (Nuevo)
- Wrapper que mantiene la misma interfaz que la versión anterior
- Usa internamente `PlaytomicAPIClient`
- Garantiza compatibilidad con el resto del sistema

### 3. `probar_reserva.py` (Actualizado)
- Script de prueba que usa el nuevo enfoque API
- Permite probar reservas sin navegador
- Más rápido y confiable

## Configuración

### Variables de Entorno Requeridas
```bash
PLAYTOMIC_EMAIL=tu_email@ejemplo.com
PLAYTOMIC_PASSWORD=tu_contraseña
PLAYTOMIC_TENANT_ID=65a5b336-e05c-4989-a3b8-3374e9ad335f
```

### IDs de Canchas Configurados
- **MONEX**: `da1fda51-61f8-4432-92b9-d93f980ed106`
- **GOCSA**: `c5270541-aeec-4640-b67d-346bd8e9d072`
- **WOODWARD**: Por configurar
- **TEDS**: Por configurar

## Ventajas del Nuevo Enfoque

### ✅ Ventajas
1. **Velocidad**: No necesita abrir navegador
2. **Confiabilidad**: No depende de elementos HTML que pueden cambiar
3. **Eficiencia**: Menor uso de recursos del sistema
4. **Mantenimiento**: Más fácil de mantener y debuggear
5. **Escalabilidad**: Puede manejar múltiples reservas simultáneas

### ❌ Desventajas
1. **Dependencia de API**: Si Playtomic cambia su API, necesitará ajustes
2. **Autenticación**: Requiere manejo manual de sesiones HTTP

## Cómo Usar

### 1. Configurar Entorno
```bash
python setup_env.py
```

### 2. Probar Conexión
```bash
python probar_reserva.py
```

### 3. Ejecutar Sistema Completo
```bash
python main.py
```

## Migración Completada

### Archivos Eliminados
- `playtomic_automation.py` (versión Selenium)
- `playtomic_automation_v2.py`
- `whatsapp_bot_selenium.py`

### Archivos Actualizados
- `main.py` - Usa nuevo sistema API
- `probar_reserva.py` - Enfoque API
- `requirements.txt` - Agregado `aiohttp`, removido Playwright
- `config.py` - Configuración para API

### Archivos Nuevos
- `playtomic_api_client.py` - Cliente API principal
- `setup_env.py` - Script de configuración
- `API_APPROACH.md` - Esta documentación

## Próximos Pasos

1. **Obtener IDs de Canchas Faltantes**: WOODWARD y TEDS
2. **Probar Reservas Reales**: Verificar que el sistema funciona
3. **Optimizar Manejo de Errores**: Mejorar respuestas de error
4. **Implementar Cache**: Para disponibilidad y sesiones

## Troubleshooting

### Error de Login
- Verificar credenciales en `.env`
- Comprobar que la cuenta esté activa

### Error de Reserva
- Verificar que la cancha esté disponible
- Comprobar formato de fecha/hora
- Revisar que el `resource_id` sea correcto

### Error de API
- Verificar conexión a internet
- Comprobar que Playtomic esté funcionando
- Revisar logs para detalles específicos
