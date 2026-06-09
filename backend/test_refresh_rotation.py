import json
import sys
import urllib.error
import urllib.request
import uuid

BASE_URL = "http://127.0.0.1:8000"


def request(method, path, payload=None):
    url = BASE_URL + path
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"error": body}
    except Exception as e:
        return None, {"error": str(e)}


def main():
    email = f"test{uuid.uuid4().hex[:8]}@example.com"
    password = "Password123"
    print("Email:", email)

    status, body = request("POST", "/api/auth/register", {"name": "Test User", "email": email, "password": password})
    print("REGISTER", status, body)

    if status not in (200, 201):
        status, body = request("POST", "/api/auth/login", {"email": "sai@example.com", "password": "Password123"})
        print("LOGIN existing", status, body)
    else:
        status, body = request("POST", "/api/auth/login", {"email": email, "password": password})
        print("LOGIN", status, body)

    if not body or "refresh_token" not in body:
        print("ERROR: no refresh token returned")
        sys.exit(1)

    old_refresh = body["refresh_token"]
    status, body = request("POST", "/api/auth/refresh", {"refresh_token": old_refresh})
    print("REFRESH 1", status, body)

    if status != 200:
        print("ERROR: first refresh failed")
        sys.exit(1)

    new_refresh = body.get("refresh_token")
    status, body = request("POST", "/api/auth/refresh", {"refresh_token": old_refresh})
    print("REFRESH reuse old", status, body)

    if new_refresh:
        status, body = request("POST", "/api/auth/refresh", {"refresh_token": new_refresh})
        print("REFRESH 2", status, body)


if __name__ == "__main__":
    main()
