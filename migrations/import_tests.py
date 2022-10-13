import os
from pathlib import Path
import re
import shutil
import subprocess


def reimport_all():
    subprocess.run(["rm", "-rf", "tests/legacy"], check=True)

    for sub_dir, _, files in os.walk("../v6_api/c2corg_api/tests"):
        dest_dir = sub_dir.replace("../v6_api/c2corg_api/tests", "c2corg_api/tests/legacy")
        Path(dest_dir).mkdir(parents=True, exist_ok=True)

        for file in files:
            if not file.endswith(".pyc"):
                source = os.path.join(sub_dir, file)
                dest = os.path.join(dest_dir, file)
                shutil.copyfile(source, dest)

    subprocess.run(["black", "c2corg_api/tests/legacy"], check=True)


def convert_test_file(filename):
    with open(filename, "r", encoding="utf-8") as f:
        code = "".join(f.readlines())

    def comment(pattern, code):
        return re.sub(f"({pattern})", r"# \1", code)

    code = code.replace("# -*- coding: utf-8 -*-\n", "")

    # remove useless lines
    code = re.sub(r"    def setUp\(self\):.*\n +super\(\w+, self\)\.setUp\(\)\n\n.   def", "\n    def", code)

    # clean unit tests code
    code = re.sub(r"def setUp\(self\):.*\n", r"def setup_method(self):\n", code)
    code = re.sub(r"def tearDown\(self\):.*\n", r"def teardown_method(self):\n", code)
    code = re.sub(r"\.setUp\(self\)", r".setup_method(self)", code)
    code = re.sub(r"\.tearDown\(self\)", r".teardown_method(self)", code)

    code = re.sub(r"self\.assertEqual\(([^,\n]*), ([^,\n]*)\)\n", r"assert \1 == \2\n", code)
    code = re.sub(r"self\.assertNotEqual\(([^,\n]*), ([^,\n]*)\)\n", r"assert \1 != \2\n", code)
    code = re.sub(r"self\.assertFalse\(([^,\n]*)\)\n", r"assert \1 is False\n", code)

    # replace imports
    code = code.replace("from c2corg_api.models.user import User", "from flask_camp.models import User")

    # replace test API
    code = re.sub(r"self\.app\.get\(", "self.get(", code)

    # rename some properties
    code = code.replace("email_validated", "email_is_validated")

    # for now, comment these imports
    code = comment(r"from c2corg_api.scripts.*\n", code)
    code = comment(r"from c2corg_api.search.*\n", code)
    code = comment(r"from c2corg_api.models.*\n", code)

    if filename.endswith("__init__.py"):
        code = re.sub("# package\n*", "", code)
        if len(code) == 0:
            return

    filename = filename.replace("legacy/", "")

    Path(os.path.dirname(filename)).mkdir(parents=True, exist_ok=True)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(code)


def convert_test_folder(folder):
    subprocess.run(["rm", "-rf", folder.replace("legacy/", "")], check=True)

    for sub_dir, _, files in os.walk(folder):
        for file in files:
            filename = os.path.join(sub_dir, file)
            dest = filename.replace("legacy/", "")

            if filename.endswith(".py"):
                convert_test_file(filename)
            else:

                Path(os.path.dirname(dest)).mkdir(parents=True, exist_ok=True)
                subprocess.run(["cp", filename, dest], check=True)


# reimport_all()
convert_test_folder("c2corg_api/tests/legacy/markdown")
convert_test_file("c2corg_api/tests/legacy/views/test_health.py")
convert_test_file("c2corg_api/tests/legacy/views/test_cooker.py")
convert_test_file("c2corg_api/tests/legacy/views/test_user.py")
