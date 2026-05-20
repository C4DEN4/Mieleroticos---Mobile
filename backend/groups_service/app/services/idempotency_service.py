import asyncio
from app.core.security import validar_uuid
from app.core.database import base_datos

class ServicioIdempotencia:
    def __init__(self):
        self._bloqueo = asyncio.Lock()

    async def es_evento_duplicado(self, id_grupo: str, id_evento: str) -> bool:
        if not validar_uuid(id_evento):
            return True

        async with self._bloqueo:
            if base_datos.evento_fue_procesado(id_grupo, id_evento):
                return True
            base_datos.registrar_evento_procesado(id_grupo, id_evento)
            return False

    async def reconocer_evento(self, id_grupo: str, id_evento: str) -> bool:
        async with self._bloqueo:
            return base_datos.reconocer_evento(id_grupo, id_evento)

    def obtener_tamano_cache(self) -> int:
        return base_datos.obtener_cantidad_eventos_procesados()

    async def limpiar_eventos_antiguos(self, horas: int = 24) -> int:
        async with self._bloqueo:
            return base_datos.limpiar_eventos_antiguos(horas)

servicio_idempotencia = ServicioIdempotencia()
