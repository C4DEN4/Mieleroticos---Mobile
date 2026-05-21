from typing import Optional, Dict
from datetime import datetime, timedelta
import asyncio
from app.core.config import configuracion
from app.core.security import generar_id_sesion
from app.core.database import base_datos
from app.models.session import CrearSesion, RespuestaSesion

class ServicioSesion:
    def __init__(self):
        self._bloqueos: Dict[str, asyncio.Lock] = {}
        self._bloqueo_global = asyncio.Lock()

    def _clave_bloqueo(self, nombre: str, id_grupo: str) -> str:
        return f"{nombre}:{id_grupo}"

    async def crear_sesion(self, datos_sesion: CrearSesion) -> RespuestaSesion:
        nombre = datos_sesion.nombre
        id_grupo = datos_sesion.id_grupo
        clave = self._clave_bloqueo(nombre, id_grupo)

        async with self._bloqueo_global:
            if clave not in self._bloqueos:
                self._bloqueos[clave] = asyncio.Lock()
            bloqueo = self._bloqueos[clave]

        async with bloqueo:
            await self.limpiar_sesiones_expiradas()

            sesion_existente = base_datos.obtener_sesion_por_nombre_y_grupo(nombre, id_grupo)
            if sesion_existente:
                raise ValueError(
                    f"El nombre '{nombre}' ya está en uso en el grupo '{id_grupo}'"
                )

            id_sesion = generar_id_sesion()
            ahora = datetime.utcnow()
            fecha_expiracion = ahora + timedelta(seconds=configuracion.sesion_ttl)

            exito = base_datos.crear_sesion(id_sesion, nombre, id_grupo, fecha_expiracion)
            if not exito:
                raise ValueError(
                    f"El nombre '{nombre}' ya está en uso en el grupo '{id_grupo}'"
                )

            sesion = {
                "id_sesion": id_sesion,
                "nombre": nombre,
                "id_grupo": id_grupo,
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
