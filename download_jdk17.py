#!/usr/bin/env python
"""Download Oracle JDK 17.0.12 ZIP and extract to project folder."""
import urllib.request
import zipfile
import os
import sys
import time

PROJECT = os.path.dirname(os.path.abspath(__file__))
ZIP_PATH = os.path.join(PROJECT, "jdk-17.0.12_windows-x64_bin.zip")
EXTRACT_DIR = PROJECT  # Extract here so we get jdk-17.0.12/ folder

# Oracle JDK 17.0.12 direct download URL
URLS = [
    "https://download.oracle.com/java/17/archive/jdk-17.0.12_windows-x64_bin.zip",
    "https://download.oracle.com/otn/java/17/archive/jdk-17.0.12_windows-x64_bin.zip",
]

def progress(block_num, block_size, total_size):
    downloaded = block_num * block_size
    if total_size > 0:
        pct = min(100, downloaded * 100 / total_size)
        mb = downloaded / (1024*1024)
        total_mb = total_size / (1024*1024)
        print(f"\r  Downloading: {mb:.1f}/{total_mb:.1f} MB ({pct:.0f}%)", end="", flush=True)

print("=" * 60)
print("DOWNLOADING ORACLE JDK 17.0.12")
print("=" * 60)

# Try each URL
downloaded = False
for url in URLS:
    print(f"\nTrying: {url}")
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            print(f"  Size: {total / (1024*1024):.1f} MB")
            
            with open(ZIP_PATH, "wb") as f:
                downloaded_bytes = 0
                while True:
                    chunk = resp.read(1024 * 1024)  # 1MB chunks
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded_bytes += len(chunk)
                    pct = (downloaded_bytes / total * 100) if total > 0 else 0
                    print(f"\r  Downloaded: {downloaded_bytes/(1024*1024):.1f} MB ({pct:.0f}%)", end="", flush=True)
            
            print(f"\n  Download complete: {downloaded_bytes/(1024*1024):.1f} MB")
            downloaded = True
            break
    except Exception as e:
        print(f"  Failed: {e}")
        continue

if not downloaded:
    print("\nAll download URLs failed.")
    print("Please download JDK 17 manually from:")
    print("  https://www.oracle.com/java/technologies/javase/jdk17-archive-downloads.html")
    print("Select 'Windows x64 Compressed Archive' (ZIP)")
    print(f"Place the ZIP at: {ZIP_PATH}")
    sys.exit(1)

# Extract
print(f"\nExtracting to: {EXTRACT_DIR}")
try:
    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        zf.extractall(EXTRACT_DIR)
    print("Extraction complete!")
    
    # Find the extracted folder
    jdk_folder = None
    for item in os.listdir(EXTRACT_DIR):
        if item.startswith("jdk-17"):
            jdk_folder = os.path.join(EXTRACT_DIR, item)
            break
    
    if jdk_folder and os.path.isdir(jdk_folder):
        java_exe = os.path.join(jdk_folder, "bin", "java.exe")
        if os.path.exists(java_exe):
            print(f"\nJDK 17 installed at: {jdk_folder}")
            print(f"Java executable: {java_exe}")
            
            # Test it
            import subprocess
            result = subprocess.run([java_exe, "-version"], capture_output=True, text=True)
            print(f"\nJava version:\n{result.stderr.strip()}")
        else:
            print(f"WARNING: java.exe not found at {java_exe}")
    else:
        # Maybe the zip contains a different folder name
        for item in os.listdir(EXTRACT_DIR):
            full = os.path.join(EXTRACT_DIR, item)
            if os.path.isdir(full) and "jdk" in item.lower():
                print(f"Found JDK folder: {item}")
                
except zipfile.BadZipFile:
    print("ERROR: Downloaded file is not a valid ZIP")
    sys.exit(1)
except Exception as e:
    print(f"Extraction failed: {e}")
    sys.exit(1)

# Cleanup
try:
    os.remove(ZIP_PATH)
    print("\nCleaned up ZIP file")
except:
    pass

print("\n" + "=" * 60)
print("DONE - Oracle JDK 17 is ready")
print("=" * 60)
