import subprocess, sys, os, time

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("Starting FastAPI backend on port 8000...")
backend = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "backend.api.main:app",
     "--host", "0.0.0.0", "--port", "8000"],
    stdout=open("backend.log", "w"),
    stderr=subprocess.STDOUT,
)
print(f"Backend PID: {backend.pid}")

time.sleep(2)

print("Starting Next.js frontend on port 3000...")
frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
npm = os.path.join(os.environ.get("PROGRAMFILES", "C:\\Program Files"), "nodejs", "npm.cmd")
frontend = subprocess.Popen(
    [npm, "run", "dev"],
    cwd=frontend_dir,
    stdout=open(os.path.join(frontend_dir, "frontend.log"), "w"),
    stderr=subprocess.STDOUT,
)
print(f"Frontend PID: {frontend.pid}")

time.sleep(5)

# Check backend
try:
    import urllib.request
    r = urllib.request.urlopen("http://localhost:8000/api/summary")
    print(f"Backend: OK (status {r.status})")
except Exception as e:
    print(f"Backend: FAILED - {e}")

# Check frontend
try:
    r = urllib.request.urlopen("http://localhost:3000")
    print(f"Frontend: OK (status {r.status})")
except Exception as e:
    print(f"Frontend: FAILED - {e}")

print("\nDashboard running at: http://localhost:3000")
print("Backend API at: http://localhost:8000")
