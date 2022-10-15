import os
from pathlib import Path
import re
import shutil
import subprocess

replacements = [
    (r"# package\n*", ""),
    (r"# -\*- coding: utf-8 -\*-\n", ""),
    # remove useless lines
    (r"    def setUp\(self\):.*\n +super\(\w+, self\)\.setUp\(\)\n\n.   def", "\n    def"),
    # not very pythonic
    (r"self\.assertTrue\((initial_encoded_password) != (modified_encoded_password)\)", r"assert \1 != \2"),
    (r'self\.assertTrue\(("\w+") in (\w+)\)', r"assert \1 in \2"),
    # clean unit tests code
    (r"def setUp\(self\):.*\n", r"def setup_method(self):\n"),
    (r"def tearDown\(self\):.*\n", r"def teardown_method(self):\n"),
    (r"\.setUp\(self\)", r".setup_method(self)"),
    (r"\.tearDown\(self\)", r".teardown_method(self)"),
    (r"self\.assertEqual\(([^,\n]*), ([^,\n]*)\)\n", r"assert \1 == \2\n"),
    (r"self\.assertEqual\(([^,\n]*), ([^,\n]*), ([^,\n]*)\)\n", r"assert \1 == \2, \3\n"),
    (r"self\.assertNotEqual\(([^,\n]*), ([^,\n]*)\)\n", r"assert \1 != \2\n"),
    (r"self\.assertFalse\(([^,\n]*)\)\n", r"assert \1 is False\n"),
    (r'self\.assertBodyEqual\((\w+), "(\w+)", "([\w @_.]+)"\)', r'assert \1.get("\2") == "\3"'),
    (r"self\.assertIn\(([^,\n]*), ([^,\n]*)\)\n", r"assert \1 in \2\n"),
    (r"self\.assertNotIn\(([^,\n]*), ([^,\n]*)\)\n", r"assert \1 not in \2\n"),
    (r"self\.assertIsNone\(([^,\n]*)\)\n", r"assert \1 is None\n"),
    (r"self\.assertIsNotNone\(([^,\n]*)\)\n", r"assert \1 is not None\n"),
    (r"self\.assertTrue\(([^,\n]*)\)\n", r"assert \1 is True\n"),
    (r"self\.assertFalse\(([^,\n]*)\)\n", r"assert \1 is False\n"),
    # imports
    (r"from c2corg_api\.models\.user import User", "from flask_camp.models import User"),
    # replace test API
    (r"self\.app\.get\(", "self.get("),
    (r"(\w+) = self\.session\.query\((\w+)\)\.get\((\w+)\)", r"\1 = self.query_get(\2, \3=\3)"),
    (r"self.session.expunge\((\w+)\)", r"self.expunge(\1)"),
    # rename some properties
    (r"user\.email_validated", "user.email_is_validated"),
    (r"user\.lang", 'user.ui_preferences["lang"]'),
    (r'json\["errors"\]\[0\]\["description"\]', 'json["description"]'),
    # remap old models
    (r"from c2corg_api.models.user_profile", r"from c2corg_api.models.legacy.user_profile"),
    # for now, comment these imports
    (r"(from c2corg_api.scripts.*\n)", r"# \1"),
    (r"(from c2corg_api.search.*\n)", r"# \1"),
    (r"(from c2corg_api.models.token.*\n)", r"# \1"),
    # targeted replace
    (r"class TestFormat\(unittest\.TestCase\):", "class TestFormat:"),
    (r'"username": "test\{\}"\.format\(i\),', '"username": forum_username,'),
    (r"(.)Shorter than minimum length 3", "r\\1'a' does not match '^[^ @\\\\\\\\/?&]{3,64}$' on instance ['name']"),
    (
        r"(.)Contain invalid character\(s\)",
        "r\\1'test/test' does not match '^[^ @\\\\\\/?&]{3,64}$' on instance ['name']",
    ),
    (r"already used forum_username", "A user still exists with this name"),
    (
        r'@patch\("c2corg_api.emails.email_service.EmailService._send_email"\)',
        '@patch("flask_camp._services._send_mail.SendMail.send_account_creation")',
    ),
    # Function that are totally replace
    (r"def extract_nonce\(", r"def extract_nonce_TO_BE_DELETED("),
    # sometime used as forum name -> back to test
    ('"testf"', '"test"'),
    ('"Max Mustermann"', '"test"'),
]


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

    subprocess.run(["black", "c2corg_api/tests"], check=True)


def convert_test_file(filename):
    with open(filename, "r", encoding="utf-8") as f:
        code = "".join(f.readlines())

    for pattern, new_value in replacements:
        code = re.sub(pattern, new_value, code)

    # remove empty init file
    if filename.endswith("__init__.py"):
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


# # reimport_all()
# convert_test_folder("c2corg_api/tests/legacy/markdown")
# convert_test_file("c2corg_api/tests/legacy/views/test_health.py")
# convert_test_file("c2corg_api/tests/legacy/views/test_cooker.py")

convert_test_file("c2corg_api/tests/legacy/views/test_user.py")

subprocess.run(["black", "c2corg_api/tests"], check=True)
