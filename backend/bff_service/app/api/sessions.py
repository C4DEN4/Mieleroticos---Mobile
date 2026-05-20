from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from app.services.client_http import cliente_http

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])
router_es = APIRouter(prefix="/api/v1/sesiones", tags=["sesiones"])

class CrearSesion(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    group_id: str = Field(..., min_length=1, max_length=50)

async def handler_crear_sesion(datos_sesion: CrearSesion):
    try:
        res = await cliente_http.crear_sesion_identidad(
            nombre=datos_sesion.name,
            id_grupo=datos_sesion.group_id
        )
        return {
            "session_id": res["id_sesion"],
            "name": res["nombre"],
            "group_id": res["id_grupo"],
            "created_at": res["fecha_creacion"],
            "expires_at": res["fecha_expiracion"]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "SESION_EXISTE",
                "mensaje": str(e),
                "codigo_estado": status.HTTP_409_CONFLICT
            }
        )
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "SERVICIO_NO_DISPONIBLE",
                "mensaje": str(e),
                "codigo_estado": status.HTTP_503_SERVICE_UNAVAILABLE
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "ERROR_INTERNO",
                "mensaje": "Error de comunicación con el servicio de identidad",
                "codigo_estado": status.HTTP_500_INTERNAL_SERVER_ERROR
            }
        )

async def handler_obtener_sesion(id_sesion: str):
    try:
        res = await cliente_http.obtener_sesion_identidad(id_sesion)
        if not res:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "SESION_NO_ENCONTRADA",
                    "mensaje": f"Sesión {id_sesion} no encontrada",
                    "codigo_estado": status.HTTP_404_NOT_FOUND
                }
            )
        return {
            "session_id": res["id_sesion"],
            "name": res["nombre"],
            "group_id": res["id_grupo"],
            "created_at": res["fecha_creacion"],
            "expires_at": res["fecha_expiracion"]
        }
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "SERVICIO_NO_DISPONIBLE",
                "mensaje": str(e),
                "codigo_estado": status.HTTP_503_SERVICE_UNAVAILABLE
            }
        )

async def handler_eliminar_sesion(id_sesion: str):
    exito = await cliente_http.eliminar_sesion_identidad(id_sesion)
    if not exito:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "SESION_NO_ENCONTRADA",
                "mensaje": f"Sesión {id_sesion} no encontrada",
                "codigo_estado": status.HTTP_404_NOT_FOUND
            }
        )

# Registrar rutas para inglés
@router.post("/", status_code=status.HTTP_201_CREATED)
async def crear_sesion(datos_sesion: CrearSesion):
    return await handler_crear_sesion(datos_sesion)

@router.get("/{id_sesion}")
async def obtener_sesion(id_sesion: str):
    return await handler_obtener_sesion(id_sesion)

@router.delete("/{id_sesion}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_sesion(id_sesion: str):
    return await handler_eliminar_sesion(id_sesion)

# Registrar rutas para español (retrocompatibilidad)
@router_es.post("/", status_code=status.HTTP_201_CREATED)
async def crear_sesion_es(datos_sesion: CrearSesion):
    return await handler_crear_sesion(datos_sesion)

@router_es.get("/{id_sesion}")
async def obtener_sesion_es(id_sesion: str):
    return await handler_obtener_sesion(id_sesion)

@router_es.delete("/{id_sesion}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_sesion_es(id_sesion: str):
    return await handler_eliminar_sesion(id_sesion)
