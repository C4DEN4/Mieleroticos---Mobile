from fastapi import APIRouter, HTTPException, status
from app.models.session import CrearSesion, RespuestaSesion, ErrorSesion
from app.services.session_service import servicio_sesion

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post(
    "/",
    response_model=RespuestaSesion,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: {"model": ErrorSesion}}
)
async def crear_sesion(datos_sesion: CrearSesion):
    try:
        sesion = await servicio_sesion.crear_sesion(datos_sesion)
        return sesion
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "SESION_EXISTE",
                "mensaje": str(e),
                "codigo_estado": status.HTTP_409_CONFLICT
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "ERROR_INTERNO",
                "mensaje": "Ocurrió un error inesperado en el servicio de identidad",
                "codigo_estado": status.HTTP_500_INTERNAL_SERVER_ERROR
            }
        )

@router.get("/{id_sesion}", response_model=RespuestaSesion)
async def obtener_sesion(id_sesion: str):
    sesion = await servicio_sesion.obtener_sesion(id_sesion)
    if not sesion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "SESION_NO_ENCONTRADA",
                "mensaje": f"Sesión {id_sesion} no encontrada o expirada",
                "codigo_estado": status.HTTP_404_NOT_FOUND
            }
        )
    return sesion

@router.delete("/{id_sesion}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_sesion(id_sesion: str):
    eliminada = await servicio_sesion.eliminar_sesion(id_sesion)
    if not eliminada:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "SESION_NO_ENCONTRADA",
                "mensaje": f"Sesión {id_sesion} no encontrada",
                "codigo_estado": status.HTTP_404_NOT_FOUND
            }
        )
