import os
from pathlib import Path
import shutil
import subprocess

subprocess.run(["rm", "-rf", "tests"], check=True)

for sub_dir, folders, files in os.walk("../v6_api/c2corg_api/tests"):
    dest_dir = sub_dir.replace("../v6_api/c2corg_api/", "")
    Path(dest_dir).mkdir(parents=True, exist_ok=True)

    for file in files:
        if not file.endswith(".pyc"):
            source = os.path.join(sub_dir, file)
            dest = os.path.join(dest_dir, file)
            shutil.copyfile(source, dest)

subprocess.run(["mv", "tests/__init__.py", "tests/__init__LEGACY.py"], check=True)
subprocess.run(["mv", "tests/markdown", "tests/test_markdown"], check=True)

subprocess.run(["black", "."], check=True)
