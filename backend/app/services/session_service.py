from typing import Optional, Dict
from datetime import datetime, timedelta
import asyncio
from app.core.config import configuracion
from app.core.security import generar_id_sesion, validar_uuid
from app.core.database import base_datos
from app.models.session import CrearSesion, RespuestaSesion


class ServicioSesion:
    """
    Servicio para gestionar sesiones de estudiantes con persistencia en SQLite.

    Implementa RQ-001: Validación de Identidad Única (Servidor)
    CA-1.1: Retorna HTTP 409 Conflict si el nombre ya existe
    CA-1.2: Mitiga condiciones de carrera para solicitudes concurrentes idénticas

    Usa SQLite para persistencia, garantizando tolerancia a fallos.
    """

    def __init__(self):
        self._bloqueos_nombre: Dict[str, asyncio.Lock] = {}
        self._bloqueo_global = asyncio.Lock()

    async def crear_sesion(self, datos_sesion: CrearSesion) -> RespuestaSesion:
        """
        Crear una nueva sesión con mitigación de condiciones de carrera.

        Usa locks por nombre para prevenir solicitudes concurrentes idénticas
        de crear sesiones duplicadas.
        """
        nombre = datos_sesion.nombre

        # Obtener o crear lock para este nombre específico
        async with self._bloqueo_global:
            if nombre not in self._bloqueos_nombre:
                self._bloqueos_nombre[nombre] = asyncio.Lock()
            bloqueo_nombre = self._bloqueos_nombre[nombre]

        # Adquirir lock específico del nombre para prevenir condiciones de carrera
        async with bloqueo_nombre:
            # Verificar si el nombre ya existe en la base de datos
            sesion_existente = base_datos.obtener_sesion_por_nombre(nombre)
            if sesion_existente:
                raise ValueError(f"Sesión con nombre '{nombre}' ya existe")

            # Crear nueva sesión
            id_sesion = generar_id_sesion()
            ahora = datetime.utcnow()
            fecha_expiracion = ahora + timedelta(seconds=configuracion.sesion_ttl)

            # Intentar insertar en la base de datos
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
        """Recuperar una sesión por ID desde la base de datos."""
        sesion = base_datos.obtener_sesion(id_sesion)
        if sesion:
            # Convertir nombres de campos para compatibilidad con modelos
            return {
                "id_sesion": sesion["session_id"],
                "nombre": sesion["name"],
                "id_grupo": sesion["group_id"],
                "fecha_creacion": datetime.fromisoformat(sesion["created_at"]),
                "fecha_expiracion": datetime.fromisoformat(sesion["expires_at"])
            }
        return None

    async def eliminar_sesion(self, id_sesion: str) -> bool:
        """Eliminar una sesión por ID de la base de datos."""
        return base_datos.eliminar_sesion(id_sesion)

    async def limpiar_sesiones_expiradas(self):
        """Eliminar todas las sesiones expiradas de la base de datos."""
        return base_datos.limpiar_sesiones_expiradas()

    def obtener_cantidad_sesiones_activas(self) -> int:
        """Obtener conteo de sesiones activas (no expiradas) desde la base de datos."""
        return base_datos.obtener_cantidad_sesiones_activas()

    async def obtener_sesiones_por_grupo(self, id_grupo: str) -> list:
        """Obtener todas las sesiones activas de un grupo desde la base de datos."""
        sesiones = base_datos.obtener_sesiones_por_grupo(id_grupo)
        return [
            {
                "id_sesion": s["session_id"],
                "nombre": s["name"],
                "id_grupo": s["group_id"],
                "fecha_creacion": datetime.fromisoformat(s["created_at"]),
                "fecha_expiracion": datetime.fromisoformat(s["expires_at"])
            }
            for s in sesiones
        ]


# Instancia global del servicio de sesión
servicio_sesion = ServicioSesion()
