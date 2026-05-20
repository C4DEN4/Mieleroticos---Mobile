import aiohttp
import asyncio
import logging
from typing import Optional, Dict
from app.core.config import configuracion

registrador = logging.getLogger(__name__)

class ClienteHTTPMicroservicios:
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def obtener_sesion(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5.0))
        return self._session

    async def cerrar(self):
        if self._session and not self._session.closed:
            await self._session.close()

    # --- Llamadas a Identity Service ---
    async def crear_sesion_identidad(self, nombre: str, id_grupo: str) -> Dict:
        """Llama al microservicio de identidad para registrar un nombre y grupo."""
        url = f"{configuracion.identity_service_url}/sessions/"
        payload = {"nombre": nombre, "id_grupo": id_grupo}
        try:
            sesion = await self.obtener_sesion()
            async with sesion.post(url, json=payload) as response:
                if response.status == 201:
                    return await response.json()
                elif response.status == 409:
                    detalles = await response.json()
                    mensaje_error = detalles.get("detail", {}).get("mensaje", "Nombre de sesión ya existe")
                    raise ValueError(mensaje_error)
                else:
                    detalles = await response.json()
                    raise Exception(f"Error de Identidad ({response.status}): {detalles}")
        except aiohttp.ClientError as e:
            registrador.error(f"Error al conectar con Identity Service: {str(e)}")
            raise ConnectionError("El microservicio de Identidad no está disponible")

    async def obtener_sesion_identidad(self, id_sesion: str) -> Optional[Dict]:
        """Llama al microservicio de identidad para obtener/validar la sesión."""
        url = f"{configuracion.identity_service_url}/sessions/{id_sesion}"
        try:
            sesion = await self.obtener_sesion()
            async with sesion.get(url) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    return None
                else:
                    return None
        except aiohttp.ClientError as e:
            registrador.error(f"Error al conectar con Identity Service para validar sesión: {str(e)}")
            raise ConnectionError("No se pudo conectar con el microservicio de Identidad")

    async def eliminar_sesion_identidad(self, id_sesion: str) -> bool:
        url = f"{configuracion.identity_service_url}/sessions/{id_sesion}"
        try:
            sesion = await self.obtener_sesion()
            async with sesion.delete(url) as response:
                return response.status == 204
        except aiohttp.ClientError:
            return False

    # --- Llamadas a Groups Service (Idempotencia) ---
    async def verificar_y_registrar_evento_grupos(self, id_grupo: str, id_evento: str) -> bool:
        """
        Llama al microservicio de grupos para registrar el evento y verificar idempotencia.
        Retorna True si el evento es duplicado, False si es nuevo.
        """
        url = f"{configuracion.groups_service_url}/groups/{id_grupo}/events/{id_evento}"
        try:
            sesion = await self.obtener_sesion()
            async with sesion.post(url) as response:
                if response.status == 200:
                    datos = await response.json()
                    return datos.get("es_duplicado", False)
                return False
        except aiohttp.ClientError as e:
            # Tolerancia a fallos: Si el microservicio de Grupos se cae,
            # degradamos la idempotencia graciosamente (permitimos el broadcast sin validación)
            registrador.warning(f"Microservicio de Grupos no disponible ({str(e)}). Degradando control de idempotencia.")
            return False  # No se considera duplicado para asegurar la entrega

    async def reconocer_evento_grupos(self, id_grupo: str, id_evento: str) -> bool:
        url = f"{configuracion.groups_service_url}/groups/{id_grupo}/events/{id_evento}"
        try:
            sesion = await self.obtener_sesion()
            async with sesion.delete(url) as response:
                return response.status == 204
        except aiohttp.ClientError:
            return False

cliente_http = ClienteHTTPMicroservicios()
