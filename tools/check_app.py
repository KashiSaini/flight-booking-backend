import traceback
from fastapi.testclient import TestClient
import sys

# ensure project root is on sys.path so `import app` works
sys.path.insert(0, r"d:\flight_booking")

try:
    from app.main import app
except Exception:
    traceback.print_exc()
    raise

client = TestClient(app)

try:
    res = client.get('/flights/')
    print('STATUS', res.status_code)
    print(res.text)
except Exception:
    traceback.print_exc()
