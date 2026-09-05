#!/usr/bin/env python
"""Start GridPulse FastAPI backend."""
import subprocess, sys, time, os

print("Starting FastAPI backend on port 8000...")
proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "backend.api.main:app",
     "--host", "0.0.0.0", "--port", "8000"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
)

# Wait a few seconds and check if it started
time.sleep(4)
if proc.poll() is None:
    print("FastAPI server is RUNNING on http://localhost:8000")
    print("PID:", proc.pid)
    # Write PID for later cleanup
    with open("backend_pid.txt", "w") as f:
        f.write(str(proc.pid))
else:
    print("Server failed to start. Output:")
    print(proc.stdout.read())
    sys.exit(1)
