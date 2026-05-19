from typing import Dict, Set, Optional
import asyncio
from datetime import datetime
from fastapi import WebSocket
from app.core.config import configuracion


class GestorConexiones:
    """
    Gestiona conexiones WebSocket con aislamiento estricto de grupos.

    Implementa RQ-003: Asignación de Nodos
    CA-3.1: Mapea y asocia en memoria cada conexión de estudiante con su ID de grupo

    Implementa RQ-004: Aislamiento Estricto de Datos
    CA-4.1: Transmisiones del Grupo A enviadas exclusivamente a WebSockets del Grupo A
    CA-4.2: Prohíbe filtración de datos entre canales de diferentes grupos
    """

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
        """
        Conectar un WebSocket y asociarlo con un grupo.

        Implementa CA-3.1: Mapeo en memoria de conexiones de estudiantes a IDs de grupo
        """
        async with self._bloqueo:
            # Almacenar conexión
            self._conexiones[id_sesion] = websocket

            # Mapear sesión a grupo
            self._grupos_sesion[id_sesion] = id_grupo
            self._nombres_sesion[id_sesion] = nombre

            # Agregar a miembros del grupo
            if id_grupo not in self._miembros_grupo:
                self._miembros_grupo[id_grupo] = set()
            self._miembros_grupo[id_grupo].add(id_sesion)

    async def desconectar(self, id_sesion: str):
        """Desconectar un WebSocket y limpiar mapeos."""
        async with self._bloqueo:
            if id_sesion in self._conexiones:
                # Obtener id_grupo antes de eliminar
                id_grupo = self._grupos_sesion.get(id_sesion)

                # Eliminar conexión
                del self._conexiones[id_sesion]

                # Eliminar del grupo
                if id_grupo and id_grupo in self._miembros_grupo:
                    self._miembros_grupo[id_grupo].discard(id_sesion)
                    # Limpiar grupos vacíos
                    if not self._miembros_grupo[id_grupo]:
                        del self._miembros_grupo[id_grupo]

                # Eliminar mapeos
                self._grupos_sesion.pop(id_sesion, None)
                self._nombres_sesion.pop(id_sesion, None)

    async def broadcast_a_grupo(self, id_grupo: str, mensaje: dict, excluir_id_sesion: Optional[str] = None):
        """
        Enviar un mensaje a todos los miembros de un grupo específico.

        Implementa CA-4.1: Aislamiento estricto - solo envía a miembros del grupo
        Implementa CA-4.2: Sin filtración de datos entre grupos
        Implementa RQ-006 CA-6.1: Latencia objetivo <500ms

        Retorna el número de receptores y la latencia en milisegundos
        """
        tiempo_inicio = datetime.utcnow()
        receptores = 0

        async with self._bloqueo:
            # Obtener miembros del grupo - aislamiento estricto
            sesiones_grupo = self._miembros_grupo.get(id_grupo, set()).copy()

        # Enviar mensajes fuera del bloqueo para minimizar contención
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
        """Enviar un mensaje a un WebSocket específico."""
        try:
            await websocket.send_json(mensaje)
        except Exception as e:
            # La conexión puede estar cerrada, se limpiará en la próxima desconexión
            pass

    async def obtener_miembros_grupo(self, id_grupo: str) -> Set[str]:
        """Obtener todos los IDs de sesión en un grupo."""
        async with self._bloqueo:
            return self._miembros_grupo.get(id_grupo, set()).copy()

    async def obtener_grupo_sesion(self, id_sesion: str) -> Optional[str]:
        """Obtener el ID de grupo para una sesión."""
        async with self._bloqueo:
            return self._grupos_sesion.get(id_sesion)

    async def obtener_nombre_sesion(self, id_sesion: str) -> Optional[str]:
        """Obtener el nombre para una sesión."""
        async with self._bloqueo:
            return self._nombres_sesion.get(id_sesion)

    def obtener_cantidad_conexiones(self) -> int:
        """Obtener el número total de conexiones activas."""
        return len(self._conexiones)

    def obtener_cantidad_grupos(self) -> int:
        """Obtener el número de grupos activos."""
        return len(self._miembros_grupo)

    async def limpiar_conexiones_obsoletas(self):
        """Limpiar conexiones obsoletas (aquellas que han sido cerradas)."""
        async with self._bloqueo:
            sesiones_obsoletas = []
            for id_sesion, websocket in self._conexiones.items():
                try:
                    # Enviar un ping para verificar si la conexión está viva
                    await websocket.ping()
                except Exception:
                    sesiones_obsoletas.append(id_sesion)

            for id_sesion in sesiones_obsoletas:
                await self.desconectar(id_sesion)


# Instancia global del gestor de conexiones
gestor_conexiones = GestorConexiones()
