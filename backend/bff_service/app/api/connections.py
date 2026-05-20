from fastapi import APIRouter
from app.services.connection_manager import gestor_conexiones

router = APIRouter(prefix="/api/v1/groups", tags=["connections"])

@router.get("/{group_id}/connections")
async def obtener_conexiones_grupo(group_id: str):
    nombres = await gestor_conexiones.obtener_nombres_grupo(group_id)
    return {
        "group_id": group_id,
        "total": len(nombres),
        "names": nombres
    }

