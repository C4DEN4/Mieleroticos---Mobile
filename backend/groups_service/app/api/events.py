from fastapi import APIRouter, HTTPException, status
from app.services.idempotency_service import servicio_idempotencia

router = APIRouter(prefix="/groups", tags=["events"])

@router.post("/{group_id}/events/{event_id}", status_code=status.HTTP_200_OK)
async def verificar_y_registrar_evento(group_id: str, event_id: str):
    es_duplicado = await servicio_idempotencia.es_evento_duplicado(group_id, event_id)
    return {
        "event_id": event_id,
        "group_id": group_id,
        "es_duplicado": es_duplicado
    }

@router.delete("/{group_id}/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def reconocer_evento(group_id: str, event_id: str):
    eliminado = await servicio_idempotencia.reconocer_evento(group_id, event_id)
    if not eliminado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evento {event_id} no encontrado"
        )
