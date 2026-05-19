import uuid
from typing import Optional
from datetime import datetime, timedelta


def generar_id_sesion() -> str:
    """Generar un ID de sesión único usando UUID v4."""
    return str(uuid.uuid4())


def generar_id_evento() -> str:
    """Generar un ID de evento único usando UUID v4 para idempotencia."""
    return str(uuid.uuid4())


def validar_uuid(cadena_uuid: str) -> bool:
    """Validar si una cadena es un UUID v4 válido."""
    try:
        obj_uuid = uuid.UUID(cadena_uuid)
        return str(obj_uuid) == cadena_uuid and obj_uuid.version == 4
    except ValueError:
        return False
