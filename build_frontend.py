import subprocess, os, sys, shutil

os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("frontend")

# Remove .next cache
if os.path.exists(".next"):
    shutil.rmtree(".next")
    print("Cleaned .next cache")

# Find npm
npm_path = None
for candidate in [
    os.path.join(os.environ.get("PROGRAMFILES", "C:\\Program Files"), "nodejs", "npm.cmd"),
    os.path.join(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"), "nodejs", "npm.cmd"),
    "npm.cmd",
    "npm",
]:
    if os.path.exists(candidate):
        npm_path = candidate
        break

if not npm_path:
    # Try where
    r = subprocess.run(["where", "npm"], capture_output=True, text=True)
    if r.returncode == 0:
        npm_path = r.stdout.strip().split("\n")[0]

print(f"npm: {npm_path}")

# Find node
node_path = None
for candidate in [
    os.path.join(os.environ.get("PROGRAMFILES", "C:\\Program Files"), "nodejs", "node.exe"),
    "node.exe",
    "node",
]:
    if os.path.exists(candidate):
        node_path = candidate
        break

if not node_path:
    r = subprocess.run(["where", "node"], capture_output=True, text=True)
    if r.returncode == 0:
        node_path = r.stdout.strip().split("\n")[0]

print(f"node: {node_path}")

# Run build
if npm_path:
    result = subprocess.run([npm_path, "run", "build"], capture_output=True, text=True, timeout=180)
    print("STDOUT:", result.stdout[-4000:] if len(result.stdout) > 4000 else result.stdout)
    print("STDERR:", result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr)
    print("RC:", result.returncode)
elif node_path:
    result = subprocess.run([node_path, "node_modules", "next", "build"], capture_output=True, text=True, timeout=180)
    print("STDOUT:", result.stdout[-4000:] if len(result.stdout) > 4000 else result.stdout)
    print("STDERR:", result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr)
    print("RC:", result.returncode)
else:
    print("ERROR: npm and node not found")
