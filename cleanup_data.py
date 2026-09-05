#!/usr/bin/env python
"""Force cleanup locked data directories."""
import os, shutil, time

BASE = os.path.dirname(os.path.abspath(__file__))
dirs = [
    os.path.join(BASE, "data", "bronze", "grid_bronze"),
    os.path.join(BASE, "data", "silver", "grid_silver"),
    os.path.join(BASE, "data", "gold"),
]

for d in dirs:
    if os.path.exists(d):
        try:
            # Remove read-only attributes
            for root, subdirs, files in os.walk(d):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        os.chmod(fp, 0o777)
                    except:
                        pass
            shutil.rmtree(d, ignore_errors=True)
            time.sleep(0.5)
            if os.path.exists(d):
                print(f"  STILL LOCKED: {d}")
            else:
                print(f"  Cleaned: {d}")
        except Exception as e:
            print(f"  Failed to clean {d}: {e}")
    else:
        print(f"  Already clean: {d}")

# Also clean any leftover PySpark temp files
for pattern in ["_SUCCESS", "._SUCCESS"]:
    for root, subdirs, files in os.walk(os.path.join(BASE, "data")):
        for f in files:
            if f == "_SUCCESS":
                fp = os.path.join(root, f)
                try:
                    os.remove(fp)
                except:
                    pass

print("\nCleanup done.")
