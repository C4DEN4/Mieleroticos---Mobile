from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CrearSesion(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    id_grupo: str = Field(..., min_length=1, max_length=50)


class RespuestaSesion(BaseModel):
    id_sesion: str
    nombre: str
    id_grupo: str
    fecha_creacion: datetime
    fecha_expiracion: datetime


class ErrorSesion(BaseModel):
    error: str
    mensaje: str
    codigo_estado: int


class MensajeWebSocket(BaseModel):
    tipo: str
    datos: dict
    marca_tiempo: datetime
    id_evento: Optional[str] = None
