import uuid

def generar_id_sesion() -> str:
    return str(uuid.uuid4())

def validar_uuid(valor: str) -> bool:
    try:
        uuid.UUID(str(valor))
        return True
    except ValueError:
        return False
