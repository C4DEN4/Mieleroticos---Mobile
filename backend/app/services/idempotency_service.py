from typing import Set, Optional
import asyncio
from app.core.security import validar_uuid
from app.core.database import base_datos


class ServicioIdempotencia:
    """
    Servicio para gestionar idempotencia y prevenir procesamiento duplicado de eventos.

    Implementa RQ-008: Idempotencia y Sincronización Post-Conexión
    CA-8.2: Valida UUIDs contra caché. Si ID existe, descarta broadcast pero confirma recepción

    Usa SQLite para persistencia, garantizando tolerancia a fallos.
    """

    def __init__(self):
        self._bloqueo = asyncio.Lock()

    async def es_evento_duplicado(self, id_evento: str) -> bool:
        """
        Verificar si un evento con el ID dado ya ha sido procesado.

        Retorna True si el evento es duplicado, False de lo contrario.
        """
        if not validar_uuid(id_evento):
            return True  # UUIDs inválidos son tratados como duplicados

        async with self._bloqueo:
            # Verificar en la base de datos
            if base_datos.evento_fue_procesado(id_evento):
                return True

            # Registrar en la base de datos
            base_datos.registrar_evento_procesado(id_evento)
            return False

    async def reconocer_evento(self, id_evento: str) -> bool:
        """
        Reconocer que un evento ha sido procesado.
        Esto es llamado por el cliente para confirmar entrega.
        """
        async with self._bloqueo:
            return base_datos.reconocer_evento(id_evento)

    def obtener_tamano_caché(self) -> int:
        """Obtener el tamaño actual de la caché de eventos procesados."""
        return base_datos.obtener_cantidad_eventos_procesados()

    async def limpiar_eventos_antiguos(self, horas: int = 24) -> int:
        """
        Limpiar eventos procesados más antiguos que el número de horas especificado.

        Retorna el número de eventos eliminados.
        """
        async with self._bloqueo:
            return base_datos.limpiar_eventos_antiguos(horas)


# Instancia global del servicio de idempotencia
servicio_idempotencia = ServicioIdempotencia()
