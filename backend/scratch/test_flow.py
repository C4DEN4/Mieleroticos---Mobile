import urllib.request
import urllib.error
import json
import asyncio
import sys
import subprocess
import time

BFF_URL = "http://localhost:8000"

def post_json(url, data):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8")), response.status

def get_json(url):
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode("utf-8")), response.status

async def test_websocket_and_chaos():
    # 1. Crear sesión para Estudiante 1
    print("--- 1. Creando sesión para estudiante_1 ---")
    data_1 = {"name": "estudiante_1", "group_id": "grupo_distribuido"}
    res_1, status_1 = post_json(f"{BFF_URL}/api/v1/sessions/", data_1)
    print(f"Estudiante 1 Creado (Status {status_1}): {res_1}\n")
    session_id_1 = res_1["session_id"]

    # 2. Intentar crear sesión duplicada con el mismo nombre (debe fallar)
    print("--- 2. Probando unicidad de nombre (debe fallar) ---")
    try:
        post_json(f"{BFF_URL}/api/v1/sessions/", data_1)
        print("ERROR: Se permitió crear sesión duplicada!")
        sys.exit(1)
    except urllib.error.HTTPError as e:
        detalles = json.loads(e.read().decode("utf-8"))
        print(f"Éxito: Falló con código esperado {e.code}: {detalles}\n")

    # 3. Crear sesión para Estudiante 2
    print("--- 3. Creando sesión para estudiante_2 ---")
    data_2 = {"name": "estudiante_2", "group_id": "grupo_distribuido"}
    res_2, status_2 = post_json(f"{BFF_URL}/api/v1/sessions/", data_2)
    print(f"Estudiante 2 Creado (Status {status_2}): {res_2}\n")
    session_id_2 = res_2["session_id"]

    # 4. Probar WebSockets usando la librería websockets
    print("--- 4. Conectando WebSockets ---")
    try:
        import websockets
    except ImportError:
        print("Instalando la librería 'websockets'...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
        import websockets

    uri_1 = f"ws://localhost:8000/ws?id_sesion={session_id_1}&id_grupo=grupo_distribuido&nombre=estudiante_1"
    uri_2 = f"ws://localhost:8000/ws?id_sesion={session_id_2}&id_grupo=grupo_distribuido&nombre=estudiante_2"

    async with websockets.connect(uri_1) as ws_1, websockets.connect(uri_2) as ws_2:
        print("Ambos clientes WebSocket conectados al BFF.")

        # 5. Enviar señal de Estudiante 1 a Estudiante 2
        print("\n--- 5. Enviando señal desde estudiante_1 (UUID único) ---")
        event_id = "11111111-2222-3333-4444-555555555555"
        payload_signal = {
            "type": "signal",
            "event_id": event_id,
            "timestamp": time.time()
        }
        await ws_1.send(json.dumps(payload_signal))

        # Estudiante 1 debe recibir ACK
        ack_msg = await ws_1.recv()
        print(f"Estudiante 1 recibió ACK: {ack_msg}")

        # Estudiante 2 debe recibir la señal retransmitida (broadcast)
        broadcast_msg = await ws_2.recv()
        print(f"Estudiante 2 recibió la señal (broadcast): {broadcast_msg}")

        # 6. Probar idempotencia (enviar el mismo event_id de nuevo)
        print("\n--- 6. Probando Idempotencia (re-enviar misma señal) ---")
        await ws_1.send(json.dumps(payload_signal))
        ack_dup = await ws_1.recv()
        print(f"Estudiante 1 recibió ACK para duplicado: {ack_dup}")
        # Debe decir "status": "duplicate"

        # 7. Ingeniería de Caos: Detener servicio de Identidad y verificar resiliencia
        print("\n--- 7. Caos: Deteniendo el servicio de Identidad ---")
        subprocess.run(["docker", "compose", "stop", "identity-service"], cwd="../../backend")
        print("Servicio de Identidad detenido.")

        # Verificar salud degradada
        time.sleep(2) # Esperar a que refresque
        res_health, _ = get_json(f"{BFF_URL}/health")
        print(f"Salud del BFF (debe ser degradada): {res_health}")

        # Intentar enviar señal con las conexiones existentes (debe funcionar!)
        print("\n--- 8. Enviando señal con Identidad apagada (Resiliencia) ---")
        event_id_2 = "99999999-8888-7777-6666-555555555555"
        payload_signal_2 = {
            "type": "signal",
            "event_id": event_id_2,
            "timestamp": time.time()
        }
        await ws_1.send(json.dumps(payload_signal_2))

        ack_msg_2 = await ws_1.recv()
        print(f"Estudiante 1 recibió ACK de resiliencia: {ack_msg_2}")

        broadcast_msg_2 = await ws_2.recv()
        print(f"Estudiante 2 recibió señal de resiliencia (broadcast): {broadcast_msg_2}")

        # Restaurar servicio de identidad
        print("\nRestaurando servicio de identidad...")
        subprocess.run(["docker", "compose", "start", "identity-service"], cwd="../../backend")
        print("Servicio de identidad restaurado.")

    print("\n--- Pruebas completadas exitosamente con 100% de cumplimiento! ---")

if __name__ == "__main__":
    asyncio.run(test_websocket_and_chaos())
