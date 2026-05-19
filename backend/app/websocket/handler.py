from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import logging
from app.services.connection_manager import gestor_conexiones
from app.services.session_service import servicio_sesion
from app.services.idempotency_service import servicio_idempotencia
from app.core.config import configuracion

registrador = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def endpoint_websocket(
    websocket: WebSocket,
    id_sesion: str = Query(...),
    id_grupo: str = Query(...),
    nombre: str = Query(...)
):
    """
    Endpoint WebSocket para comunicación en tiempo real.

    Implementa RQ-005: Conexión Concurrente Masiva
    CA-5.1: Soporta conexión simultánea de >40 dispositivos sin degradación

    Implementa RQ-006: Retransmisión de Señales (Broadcast)
    CA-6.1: Latencia <500ms para propagación de señales
    CA-6.2: Renderizado dinámico de texto de notificación
    """
    # Validar sesión
    sesion = await servicio_sesion.obtener_sesion(id_sesion)
    if not sesion:
        await websocket.close(code=4001, reason="Sesión inválida o expirada")
        return

    # Verificar que la sesión coincida con los parámetros proporcionados
    if sesion["id_grupo"] != id_grupo or sesion["nombre"] != nombre:
        await websocket.close(code=4002, reason="Parámetros de sesión no coinciden")
        return

    # Verificar límite de conexiones
    if gestor_conexiones.obtener_cantidad_conexiones() >= configuracion.ws_max_conexiones:
        await websocket.close(code=4003, reason="Máximo de conexiones alcanzado")
        return

    # Aceptar conexión
    await websocket.accept()

    # Registrar conexión
    await gestor_conexiones.conectar(id_sesion, id_grupo, nombre, websocket)
    registrador.info(f"WebSocket conectado: id_sesion={id_sesion}, id_grupo={id_grupo}, nombre={nombre}")

    try:
        while True:
            # Recibir mensaje del cliente
            datos = await websocket.receive_json()

            # Procesar mensaje
            await manejar_mensaje_websocket(websocket, id_sesion, id_grupo, nombre, datos)

    except WebSocketDisconnect:
        registrador.info(f"WebSocket desconectado: id_sesion={id_sesion}")
    except Exception as e:
        registrador.error(f"Error de WebSocket para id_sesion={id_sesion}: {str(e)}")
    finally:
        # Limpiar conexión
        await gestor_conexiones.desconectar(id_sesion)
        registrador.info(f"WebSocket limpiado: id_sesion={id_sesion}")


async def manejar_mensaje_websocket(
    websocket: WebSocket,
    id_sesion: str,
    id_grupo: str,
    nombre: str,
    datos: dict
):
    """
    Manejar mensajes WebSocket entrantes.

    Implementa RQ-008: Idempotencia y Sincronización Post-Conexión
    CA-8.2: Valida UUIDs contra caché
    """
    tipo_mensaje = datos.get("type")

    if tipo_mensaje == "signal":
        # Manejar broadcast de señal
        id_evento = datos.get("event_id")

        # Verificar evento duplicado (idempotencia)
        es_duplicado = await servicio_idempotencia.es_evento_duplicado(id_evento)

        if es_duplicado:
            # Evento duplicado - reconocer pero no hacer broadcast
            await websocket.send_json({
                "type": "ack",
                "event_id": id_evento,
                "status": "duplicate",
                "message": "Evento ya procesado"
            })
            return

        # Broadcast al grupo (excluyendo remitente)
        # Implementa CA-6.2: Renderizado dinámico con nombre del estudiante
        mensaje_broadcast = {
            "type": "notification",
            "data": {
                "message": f"{nombre} ha enviado una señal!",
                "sender_name": nombre,
                "timestamp": datos.get("timestamp")
            },
            "event_id": id_evento
        }

        receptores, latencia_ms = await gestor_conexiones.broadcast_a_grupo(
            id_grupo,
            mensaje_broadcast,
            excluir_id_sesion=id_sesion
        )

        # Reconocer al remitente
        await websocket.send_json({
            "type": "ack",
            "event_id": id_evento,
            "status": "success",
            "recipients": receptores,
            "latency_ms": latencia_ms
        })

        registrador.info(
            f"Broadcast de señal: grupo={id_grupo}, remitente={nombre}, "
            f"receptores={receptores}, latencia={latencia_ms:.2f}ms"
        )

    elif tipo_mensaje == "ack":
        # Manejar reconocimiento del cliente
        id_evento = datos.get("event_id")
        await servicio_idempotencia.reconocer_evento(id_evento)

    elif tipo_mensaje == "ping":
        # Responder a ping
        await websocket.send_json({"type": "pong"})

    else:
        # Tipo de mensaje desconocido
        await websocket.send_json({
            "type": "error",
            "message": f"Tipo de mensaje desconocido: {tipo_mensaje}"
        })
