import os
from pathlib import Path
import re
import black
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
    (r'self\.assertBodyEqual\((\w+), "(\w+)", (\w+)\)', r'assert \1.get("\2") == \3'),
    (r"self\.assertIn\(([^,\n]*), ([^,\n]*)\)\n", r"assert \1 in \2\n"),
    (r"self\.assertNotIn\(([^,\n]*), ([^,\n]*)\)\n", r"assert \1 not in \2\n"),
    (r"self\.assertIsNone\(([^,\n]*)\)\n", r"assert \1 is None\n"),
    (r"self\.assertIsNotNone\(([^,\n]*)\)\n", r"assert \1 is not None\n"),
    (r"self\.assertTrue\(([^,\n]*)\)\n", r"assert \1 is True\n"),
    (r"self\.assertFalse\(([^,\n]*)\)\n", r"assert \1 is False\n"),
    # replace test API
    (r"self\.app\.get\(", "self.get("),
    (r"(\w+) = self\.session\.query\((\w+)\)\.get\((\w+)\)", r"\1 = self.query_get(\2, \3=\3)"),
    (
        r'query = self.session.query\(User\).filter\(User.username == "test"\)',
        r'query = self.session.query(NewUser).filter(NewUser.name == "test")',
    ),
    (r"self.session.expunge\((\w+)\)", r"self.expunge(\1)"),
    (r"= search_documents\[(\w+)\].get\(", r"= self.search_document(\1, "),
    (r"self\.search_document\(USERPROFILE_TYPE, id=user_id", r"self.search_document(USERPROFILE_TYPE, user_id=user_id"),
    # rename some properties
    (r'json\["errors"\]\[0\]\["description"\]', 'json["description"]'),
    (r"purge_account\(self\.session\)", "purge_account()"),
    # remap old models to legacy model
    (r"from c2corg_api.models\.user_profile ", r"from c2corg_api.legacy.models.user_profile "),
    (
        r"from c2corg_api\.models\.user ",
        "from flask_camp.models import User as NewUser\nfrom c2corg_api.legacy.models.user ",
    ),
    (r"from c2corg_api.scripts.es.sync ", "from c2corg_api.legacy.scripts.es.sync "),
    (r"from c2corg_api.search ", "from c2corg_api.legacy.search "),
    # for now, comment these imports
    (r"(from c2corg_api.models.token.*\n)", r"# \1"),
    # targeted replace
    (r"class TestFormat\(unittest\.TestCase\):", "class TestFormat:"),
    (r'"username": "test\{\}"\.format\(i\),', '"username": forum_username,'),
    (r"(.)Shorter than minimum length 3", "r\\1'a' does not match '^[^ @\\\\\\\\/?&]{3,64}$' on instance ['name']"),
    (
        r"(.)Contain invalid character\(s\)",
        "r\\1'test/test' does not match '^[^ @\\\\\\/?&]{3,64}$' on instance ['name']",
    ),
    (
        r'self\.session\.query\(User\)\.filter\(User.username == "moderator"\).one\(\)',
        r'self.session.query(NewUser).filter(NewUser.name == "moderator").one()',
    ),
    # (r"test_login_blocked_account(.*\n *).*\n", r'test_login_blocked_account\1contributor = NewUser.get(name="contributor")\n'),
    (r"already used forum_username", "A user still exists with this name"),
    (
        r'@patch\("c2corg_api.emails.email_service.EmailService._send_email"\)',
        '@patch("flask_camp._services._send_mail.SendMail.send")',
    ),
    (r"from datetime import datetime\n", "from datetime import datetime, timedelta\n"),
    (r"user.validation_nonce_expire = now", "user.creation_date = now - timedelta(days=3)"),
    # Function that are totally replaced
    (r"def extract_nonce\(", r"def extract_nonce_TO_BE_DELETED("),
    # sometime used as forum name -> back to test
    ('"testf"', '"test"'),
    # ('"Max Mustermann"', '"test"'),
    ('"Contributor"', '"contributor"'),
    # search title_fr was v6 name + forum_username. It now only name
    ('"Max Mustermann testf"', '"test"'),
    ('"changed contributor"', '"contributor"'),
    # errors in v6_api
    ("sso_sync", "sync_sso"),
    # different behavior
    (r'(self.app_post_json\(url, \{"email": "non_existing_oeuhsaeuh@camptocamp.org"\}, status)=400', r"\1=200"),
    (r'self\.assertErrorsContain\(body, "email", "No user with this email"\)', ""),
]

skipped_methods = {
    "test_purge_tokens": "No such model in flask_camp",
    "test_renew_success": "/renew is not used",
    "test_renew_token_different_success": "/renew is not used",
    "test_login_blocked_account": "blocked users can log-in",
    "test_login_discourse_success": "sso in login payload not used anymore?",
    "test_read_account_info_blocked_account": "blocked users can view their account",
}


def convert_test_file(filename):
    with open(f"../v6_api/c2corg_api/tests/{filename}", "r", encoding="utf-8") as f:
        code = "".join(f.readlines())

    code = black.format_str(code, mode=black.Mode(line_length=120))

    for pattern, new_value in replacements:
        code = re.sub(pattern, new_value, code)

    for method, skip_reason in skipped_methods.items():
        code = code.replace(
            f"\n    def {method}(self",
            f'\n    @pytest.mark.skip(reason="{skip_reason}")\n    def {method}(self',
        )

    code = black.format_str(code, mode=black.Mode(line_length=120))

    # remove empty init file
    if filename.endswith("__init__.py"):
        if len(code) == 0:
            return

    code = f"import pytest\n{code}"

    dest = f"c2corg_api/tests/{filename}"
    Path(os.path.dirname(dest)).mkdir(parents=True, exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(code)


def convert_test_folder(folder):
    subprocess.run(["rm", "-rf", f"c2corg_api/tests/{folder}"], check=True)

    for sub_dir, _, files in os.walk(f"../v6_api/c2corg_api/tests/{folder}"):
        for file in files:
            filename = os.path.join(sub_dir, file)

            if filename.endswith(".py"):
                convert_test_file(filename.replace("../v6_api/c2corg_api/tests/", ""))
            else:
                dest = filename.replace("../v6_api/", "")
                Path(os.path.dirname(dest)).mkdir(parents=True, exist_ok=True)
                subprocess.run(["cp", filename, dest], check=True)


# convert_test_folder("markdown")
convert_test_file("views/test_health.py")
convert_test_file("views/test_cooker.py")
convert_test_file("views/test_user.py")
convert_test_file("views/test_user_account.py")
