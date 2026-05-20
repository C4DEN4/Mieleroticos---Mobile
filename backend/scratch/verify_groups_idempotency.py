import json
import uuid
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8002"


def _request(method: str, path: str):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read()
            return resp.status, body
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def main():
    group_a = "grupo-a"
    group_b = "grupo-b"
    event_id = str(uuid.uuid4())

    status, body = _request("POST", f"/groups/{group_a}/events/{event_id}")
    print("POST A (first):", status, body.decode("utf-8"))

    status, body = _request("POST", f"/groups/{group_a}/events/{event_id}")
    print("POST A (duplicate):", status, body.decode("utf-8"))

    status, body = _request("POST", f"/groups/{group_b}/events/{event_id}")
    print("POST B (same event_id):", status, body.decode("utf-8"))

    status, body = _request("DELETE", f"/groups/{group_a}/events/{event_id}")
    print("DELETE A:", status, body.decode("utf-8"))

    try:
        payload = json.loads(body.decode("utf-8") or "null")
    except json.JSONDecodeError:
        payload = None

    if payload is not None:
        print("Nota: DELETE devolvio cuerpo inesperado.")


if __name__ == "__main__":
    main()

