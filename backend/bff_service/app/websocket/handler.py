from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import logging
from app.services.connection_manager import gestor_conexiones
from app.services.client_http import cliente_http
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
    registrador.info(
        f"Intento WebSocket: id_sesion={id_sesion}, id_grupo={id_grupo}, nombre={nombre}"
    )
    try:
        sesion = await cliente_http.obtener_sesion_identidad(id_sesion)
    except ConnectionError:
        await websocket.close(code=4004, reason="Servicio de Identidad no disponible")
        return

    if not sesion:
        await websocket.close(code=4001, reason="Sesión inválida o expirada")
        return

    if sesion["id_grupo"] != id_grupo or sesion["nombre"] != nombre:
        await websocket.close(code=4002, reason="Parámetros de sesión no coinciden")
        return

    if gestor_conexiones.obtener_cantidad_conexiones() >= configuracion.ws_max_conexiones:
        await websocket.close(code=4003, reason="Máximo de conexiones alcanzado")
        return

    await websocket.accept()
    await gestor_conexiones.conectar(id_sesion, id_grupo, nombre, websocket)
    registrador.info(f"WebSocket conectado al BFF: id_sesion={id_sesion}, id_grupo={id_grupo}, nombre={nombre}")

    try:
        while True:
            datos = await websocket.receive_json()
            await manejar_mensaje_websocket(websocket, id_sesion, id_grupo, nombre, datos)

    except WebSocketDisconnect:
        registrador.info(f"WebSocket desconectado del BFF: id_sesion={id_sesion}")
    except Exception as e:
        registrador.error(f"Error de WebSocket para id_sesion={id_sesion}: {str(e)}")
    finally:
        await gestor_conexiones.desconectar(id_sesion)
        registrador.info(f"WebSocket limpiado en el BFF: id_sesion={id_sesion}")

async def manejar_mensaje_websocket(
    websocket: WebSocket,
    id_sesion: str,
    id_grupo: str,
    nombre: str,
    datos: dict
):
    tipo_mensaje = datos.get("type")

    if tipo_mensaje == "signal":
        id_evento = datos.get("event_id")
        es_duplicado = await cliente_http.verificar_y_registrar_evento_grupos(id_grupo, id_evento)

        if es_duplicado:
            await websocket.send_json({
                "type": "ack",
                "event_id": id_evento,
                "status": "duplicate",
                "message": "Evento ya procesado"
            })
            return

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

        await websocket.send_json({
            "type": "ack",
            "event_id": id_evento,
            "status": "success",
            "recipients": receptores,
            "latency_ms": latencia_ms
        })

        registrador.info(
            f"Broadcast de señal distribuida: grupo={id_grupo}, remitente={nombre}, "
            f"receptores={receptores}, latencia={latencia_ms:.2f}ms"
        )

    elif tipo_mensaje == "ack":
        id_evento = datos.get("event_id")
        await cliente_http.reconocer_evento_grupos(id_grupo, id_evento)

    elif tipo_mensaje == "ping":
        await websocket.send_json({"type": "pong"})

    else:
        await websocket.send_json({
            "type": "error",
            "message": f"Tipo de mensaje desconocido: {tipo_mensaje}"
        })
