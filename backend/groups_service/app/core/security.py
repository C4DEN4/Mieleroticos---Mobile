import uuid

def validar_uuid(valor: str) -> bool:
    try:
        uuid.UUID(str(valor))
        return True
    except ValueError:
        return False
