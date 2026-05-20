from typing import Optional, Dict
from datetime import datetime, timedelta
import asyncio
from app.core.config import configuracion
from app.core.security import generar_id_sesion
from app.core.database import base_datos
from app.models.session import CrearSesion, RespuestaSesion

class ServicioSesion:
    def __init__(self):
        self._bloqueos_nombre: Dict[str, asyncio.Lock] = {}
        self._bloqueo_global = asyncio.Lock()

    async def crear_sesion(self, datos_sesion: CrearSesion) -> RespuestaSesion:
        nombre = datos_sesion.nombre

        async with self._bloqueo_global:
            if nombre not in self._bloqueos_nombre:
                self._bloqueos_nombre[nombre] = asyncio.Lock()
            bloqueo_nombre = self._bloqueos_nombre[nombre]

        async with bloqueo_nombre:
            sesion_existente = base_datos.obtener_sesion_por_nombre(nombre)
            if sesion_existente:
                raise ValueError(f"Sesión con nombre '{nombre}' ya existe")

            id_sesion = generar_id_sesion()
            ahora = datetime.utcnow()
            fecha_expiracion = ahora + timedelta(seconds=configuracion.sesion_ttl)

            exito = base_datos.crear_sesion(id_sesion, nombre, datos_sesion.id_grupo, fecha_expiracion)
            if not exito:
                raise ValueError(f"Sesión con nombre '{nombre}' ya existe")

            sesion = {
                "id_sesion": id_sesion,
                "nombre": nombre,
                "id_grupo": datos_sesion.id_grupo,
                "fecha_creacion": ahora,
                "fecha_expiracion": fecha_expiracion
            }
            return RespuestaSesion(**sesion)

    async def obtener_sesion(self, id_sesion: str) -> Optional[Dict]:
        sesion = base_datos.obtener_sesion(id_sesion)
        if sesion:
            return {
                "id_sesion": sesion["session_id"],
                "nombre": sesion["name"],
                "id_grupo": sesion["group_id"],
                "fecha_creacion": datetime.fromisoformat(sesion["created_at"]),
                "fecha_expiracion": datetime.fromisoformat(sesion["expires_at"])
            }
        return None

    async def eliminar_sesion(self, id_sesion: str) -> bool:
        return base_datos.eliminar_sesion(id_sesion)

    async def limpiar_sesiones_expiradas(self):
        return base_datos.limpiar_sesiones_expiradas()

    def obtener_cantidad_sesiones_activas(self) -> int:
        return base_datos.obtener_cantidad_sesiones_activas()

servicio_sesion = ServicioSesion()
