import subprocess
import sys
import os

# Start uvicorn in background
env = os.environ.copy()
env["PYTHONPATH"] = r"E:\files\backend:" + env.get("PYTHONPATH", "")

proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
    cwd=r"E:\files\backend",
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
)

print(f"Uvicorn started with PID {proc.pid}")
print(f"Waiting for startup...")
import time
time.sleep(3)

# Test health endpoint
import urllib.request
try:
    req = urllib.request.Request("http://localhost:8000/health")
    with urllib.request.urlopen(req, timeout=5) as response:
        print(f"Health check: {response.status_code} {response.read().decode()}")
except Exception as e:
    print(f"Health check failed: {e}")