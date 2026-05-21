from typing import Dict, Set, Optional
import asyncio
from datetime import datetime
from fastapi import WebSocket

class GestorConexiones:
    def __init__(self):
        # Mapa id_sesion -> conexión WebSocket
        self._conexiones: Dict[str, WebSocket] = {}

        # Mapa id_grupo -> conjunto de ids_sesion
        self._miembros_grupo: Dict[str, Set[str]] = {}

        # Mapa id_sesion -> id_grupo
        self._grupos_sesion: Dict[str, str] = {}

        # Mapa id_sesion -> nombre
        self._nombres_sesion: Dict[str, str] = {}

        self._bloqueo = asyncio.Lock()

    async def conectar(self, id_sesion: str, id_grupo: str, nombre: str, websocket: WebSocket):
        async with self._bloqueo:
            if id_sesion in self._conexiones:
                conexion_anterior = self._conexiones[id_sesion]
                if conexion_anterior is not websocket:
                    try:
                        await conexion_anterior.close(code=1000, reason="Reemplazada por nueva conexion")
                    except Exception:
                        pass

            self._conexiones[id_sesion] = websocket
            self._grupos_sesion[id_sesion] = id_grupo
            self._nombres_sesion[id_sesion] = nombre

            if id_grupo not in self._miembros_grupo:
                self._miembros_grupo[id_grupo] = set()
            self._miembros_grupo[id_grupo].add(id_sesion)

    async def desconectar(self, id_sesion: str):
        async with self._bloqueo:
            if id_sesion in self._conexiones:
                id_grupo = self._grupos_sesion.get(id_sesion)
                del self._conexiones[id_sesion]

                if id_grupo and id_grupo in self._miembros_grupo:
                    self._miembros_grupo[id_grupo].discard(id_sesion)
                    if not self._miembros_grupo[id_grupo]:
                        del self._miembros_grupo[id_grupo]

                self._grupos_sesion.pop(id_sesion, None)
                self._nombres_sesion.pop(id_sesion, None)

    async def broadcast_a_grupo(self, id_grupo: str, mensaje: dict, excluir_id_sesion: Optional[str] = None):
        tiempo_inicio = datetime.utcnow()
        receptores = 0

        async with self._bloqueo:
            sesiones_grupo = self._miembros_grupo.get(id_grupo, set()).copy()

        tareas = []
        for id_sesion in sesiones_grupo:
            if id_sesion != excluir_id_sesion:
                websocket = self._conexiones.get(id_sesion)
                if websocket:
                    tareas.append(self._enviar_mensaje(websocket, mensaje))
                    receptores += 1

        if tareas:
            await asyncio.gather(*tareas, return_exceptions=True)

        tiempo_fin = datetime.utcnow()
        latencia_ms = (tiempo_fin - tiempo_inicio).total_seconds() * 1000

        return receptores, latencia_ms

    async def _enviar_mensaje(self, websocket: WebSocket, mensaje: dict):
        try:
            await websocket.send_json(mensaje)
        except Exception:
            pass

    def obtener_cantidad_conexiones(self) -> int:
        return len(self._conexiones)

    def obtener_cantidad_grupos(self) -> int:
        return len(self._miembros_grupo)

    async def obtener_nombres_grupo(self, id_grupo: str):
        async with self._bloqueo:
            sesiones_grupo = self._miembros_grupo.get(id_grupo, set()).copy()
            nombres = {self._nombres_sesion.get(id_sesion) for id_sesion in sesiones_grupo}
        return sorted({nombre for nombre in nombres if nombre})

gestor_conexiones = GestorConexiones()
