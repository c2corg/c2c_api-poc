#!/usr/bin/env python3

import os
from pathlib import Path
import re
import black
import subprocess


def get_code(filename):
    with open(f"../v6_api/c2corg_api/tests/{filename}", "r", encoding="utf-8") as f:
        code = "".join(f.readlines())

    return black.format_str(code, mode=black.Mode(line_length=120))


def _get_python_value():
    dict_member = r"\w+(?:\[(?:\"\w+\"|\d+)\])+"
    simple_value = r"[^,\n\]\[]+"
    string_list = r'\["\w+"(?:, "\w+")*\]'
    function_call = r"[^\n(]+\([^\n)]*\)"

    return f"({dict_member}|{simple_value}|{string_list}|{function_call})"


def _assert_replacements(old_foo, operator):
    value = _get_python_value()
    comment = r"([^,\n\)]*)"

    return [
        (rf"self\.{old_foo}\({value}, {value}\)\n", rf"assert \1 {operator} \2\n"),
        (rf"self\.{old_foo}\({value}, {value}, {comment}\)\n", rf"assert \1 {operator} \2, \3\n"),
    ]


def _assert_unary_replacements(old_foo, operator):
    value = _get_python_value()
    comment = r"([^,\n\)]*)"

    return [
        (rf"self\.{old_foo}\({value}\)\n", rf"assert \1 {operator}\n"),
        (rf"self\.{old_foo}\({value}, {comment}\)\n", rf"assert \1 {operator}, \2\n"),
    ]


replacements = (
    [
        (r"# package\n*", ""),
        (r"# -\*- coding: utf-8 -\*-\n", ""),
        # remove useless lines
        (r"    def setUp\(self\):.*\n +super\(\w+, self\)\.setUp\(\)\n\n.   def", "\n    def"),
        (r"(    def setUp\(self\):.*\n +)super\(\w+, self\)\.setUp\(\)\n", r"\1super().setUp()\n"),
        # not very pythonic
        (r"self\.assertTrue\((initial_encoded_password) != (modified_encoded_password)\)", r"assert \1 != \2"),
        (r'self\.assertTrue\(("\w+") in (\w+)\)', r"assert \1 in \2"),
        # rename some properties
        (r'json\["errors"\]\[0\]\["description"\]', 'json["description"]'),
        # clean unit tests code
        (r"def setUp\(self\):.*\n", r"def setup_method(self):\n"),
        (r"def tearDown\(self\):.*\n", r"def teardown_method(self):\n"),
        (r"\.setUp\(self\)", r".setup_method(self)"),
        (r"\.setUp\(\)", r".setup_method()"),
        (r"\.tearDown\(self\)", r".teardown_method(self)"),
    ]
    + _assert_replacements("assertEqual", "==")
    + _assert_replacements("assertNotEqual", "!=")
    + _assert_replacements("assertIn", "in")
    + _assert_replacements("assertNotIn", "not in")
    + _assert_unary_replacements("assertIsNone", "is None")
    + _assert_unary_replacements("assertIsNotNone", "is not None")
    + _assert_unary_replacements("assertFalse", "is False")
    + _assert_unary_replacements("assertTrue", "is True")
    + [
        (r'self\.assertBodyEqual\((\w+), "(\w+)", "([\w @_.]+)"\)', r'assert \1.get("\2") == "\3"'),
        (r'self\.assertBodyEqual\((\w+), "(\w+)", (\w+)\)', r'assert \1.get("\2") == \3'),
        (r"self\.assertIsInstance\(", "assert isinstance("),
        # replace test API
        (r"self\.session\.refresh\(", r"self.session_refresh("),
        (r"self\.get\((.*)\)\n", r"self.get_custom(\1)\n"),
        (r"self\.app\.get\((.*)\)\n", r"self.get(\1)\n"),
        (r"self\.app\.post_json\((.*)\)\n", r"self.post_json(\1)\n"),
        (r"(\w+) = self\.session\.query\((\w+)\)\.get\((\w+)\)", r"\1 = self.query_get(\2, \3=\3)"),
        (
            r'query = self.session.query\(User\).filter\(User.username == "test"\)',
            r'query = self.session.query(NewUser).filter(NewUser.name == "test")',
        ),
        (r"self.session.expunge\((\w+)\)", r"self.expunge(\1)"),
        (r"= search_documents\[(\w+)\].get\(", r"= self.search_document(\1, "),
        (
            r"self\.search_document\(USERPROFILE_TYPE, id=user_id",
            r"self.search_document(USERPROFILE_TYPE, user_id=user_id",
        ),
        (r"self\.session\.add_all\(", "self.session_add_all("),
        (r"self\.session\.add\(", "self.session_add("),
        (r"purge_account\(self\.session\)", "purge_account()"),
        # remap old models to legacy model
        (r"from c2corg_api.models\.user_profile ", r"from c2corg_api.legacy.models.user_profile "),
        (
            r"from c2corg_api\.models\.user ",
            "from flask_camp.models import User as NewUser\nfrom c2corg_api.legacy.models.user ",
        ),
        (r"from c2corg_api.scripts.es.sync ", "from c2corg_api.legacy.scripts.es.sync "),
        (r"from c2corg_api.search ", "from c2corg_api.legacy.search "),
        (r"from c2corg_api.models.feed ", "from c2corg_api.legacy.models.feed "),
        (r"from c2corg_api.models.document ", "from c2corg_api.legacy.models.document "),
        (r"from c2corg_api.models.area ", "from c2corg_api.legacy.models.area "),
        (r"from c2corg_api.views.user_follow import", "from c2corg_api.legacy.views.user_follow import"),
        (
            r"from c2corg_api.tests.views import BaseTestRest\n",
            "from c2corg_api.tests.legacy.views import BaseTestRest\n",
        ),
        (r"from c2corg_api.tests.views.test_user", "from c2corg_api.tests.legacy.views.test_user"),
        (r"from c2corg_api.models.mailinglist", "from c2corg_api.legacy.models.mailinglist"),
        (
            r"from c2corg_api.search.mappings.user_mapping import SearchUser",
            "from c2corg_api.legacy.search import SearchUser",
        ),
        (r"from c2corg_api.views.document import", "from c2corg_api.legacy.views.document import"),
        (
            r"from c2corg_api.tests.views import BaseDocumentTestRest\n",
            "from c2corg_api.tests.legacy.views import BaseDocumentTestRest\n",
        ),
        # for now, comment these imports
        (r"(from c2corg_api.models.token.*\n)", r"# \1"),
        (r"(from c2corg_api.models.common.attributes import mailinglists\n)", r"# \1"),
        (
            r"from c2corg_api.tests.search import reset_search_index\n",
            r"from c2corg_api.tests.legacy.search import reset_search_index\n",
        ),
        # targeted replace
        (
            r'self\.session\.query\(User\)\.get\(self\.global_userids\["(\w+)"\]\)',
            r'self.query_get(User, user_id=self.global_userids["\1"])',
        ),
        (r"class TestFormat\(unittest\.TestCase\):", "class TestFormat:"),
        (r'"username": "test\{\}"\.format\(i\),', '"username": forum_username,'),
        (
            r'self\.session\.query\(User\)\.filter\(User.username == "moderator"\).one\(\)',
            r'self.session.query(NewUser).filter(NewUser.name == "moderator").one()',
        ),
        (r"already used forum_username", "A user still exists with this name"),
        (
            r'@patch\("c2corg_api.emails.email_service.EmailService._send_email"\)',
            '@patch("flask_camp._services._send_mail.SendMail.send")',
        ),
        (r"from datetime import datetime\n", "from datetime import datetime, timedelta\n"),
        (r"user.validation_nonce_expire = now", "user.creation_date = now - timedelta(days=3)"),
        (
            r'errors = body.get\("errors"\)\n {8}assert self\.get_error\(errors, "user_id"\)',
            r'assert self.get_body_error(body, "user_id")',
        ),
        (r" *assert .*\.ratelimit_times.*\n", ""),
        (r"(class BaseBlockTest(?:.|\n)*self\.session\.)flush", r"\1commit"),
        (
            r'(assert json\["description"\] == )"Invalid email address"',
            "\\1\"'some_useratcamptocamp.org' is not a 'email' on instance ['user']['email']\"",
        ),
        # Function that are totally replaced
        (r"def extract_nonce\(", r"def extract_nonce_TO_BE_DELETED("),
        # sometime used as forum name -> back to test
        ('"testf"', '"test"'),
        ('"Contributor"', '"contributor"'),
        # search title_fr was v6 name + forum_username. It now only name
        ('"Max Mustermann testf"', '"test"'),
        ('"changed contributor"', '"contributor"'),
        # errors in v6_api
        ("sso_sync", "sync_sso"),
        # different behavior
        (r'(self.app_post_json\(url, \{"email": "non_existing_oeuhsaeuh@camptocamp.org"\}, status)=400', r"\1=200"),
        (r'self\.assertErrorsContain\(body, "email", "No user with this email"\)', ""),
        # error messages
        ('"Already used forum name"', '"Name or email already exists"'),
    ]
)

skipped_methods = {
    "test_purge_tokens": "No such model in flask_camp",
    "test_renew_success": "/renew is not used",
    "test_renew_token_different_success": "/renew is not used",
    "test_login_blocked_account": "blocked users can log-in",
    "test_login_discourse_success": "sso in login payload not used anymore?",
    "test_read_account_info_blocked_account": "blocked users can view their account",
    "test_post_preferences_invalid": "Too painful to automatically import, recoded it",
    "test_post_preferences": "Too painful to automatically import, recoded it",
    "test_register_username_email_not_equals_email": "username is removed in new model",
    "test_get_collection_paginated": "unecessary complexity of profile with no validated email, recoded it",
    "test_get_unconfirmed_user": "unecessary complexity of profile with no validated email, recoded it",
    "test_get_unauthenticated_private_profile": "useless feature: anybody can create a profile to see profile",
    "test_get_caching": "caching is handled and tested in flask-camp",
    "test_get_info": "test_get_info is not used in UI",
    "test_put_wrong_locale_version": "Locales are not versionned in the new model",
}

skipped_classes = {
    "TestUserBlockedRest": "Redundant, and not used in actual UI",
    "TestUserBlockedAllRest": "Not used in actual UI",
    "TestUserFollowRest": "PITA, rewrite it",
    "TestUserUnfollowRest": "PITA, rewrite it",
    "TestUserFollowingUserRest": "Not used in actual UI",
    "TestUserFollowingRest": "Not used in actual UI",
    "TestUserMailinglistsRest": "Not used in actual UI",
}


def convert_test_file(filename, make_replacements=True):

    code = get_code(filename)

    if make_replacements:
        for pattern, new_value in replacements:
            code = re.sub(pattern, new_value, code)

        for method, skip_reason in skipped_methods.items():
            code = code.replace(
                f"\n    def {method}(self",
                f'\n    @pytest.mark.skip(reason="{skip_reason}")\n    def {method}(self',
            )

        for klass, skip_reason in skipped_classes.items():
            code = code.replace(
                f"\nclass {klass}(",
                f'\n@pytest.mark.skip(reason="{skip_reason}")\ndef {klass}(',
            )

        code = black.format_str(code, mode=black.Mode(line_length=120))

        # remove empty init file
        if filename.endswith("__init__.py"):
            if len(code) == 0:
                return

        code = f"import pytest\n{code}"

    dest = f"c2corg_api/tests/legacy/{filename}"
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
convert_test_file("views/test_user_preferences.py")
convert_test_file("views/test_user_block.py")
convert_test_file("views/test_user_follow.py")
convert_test_file("views/test_user_mailinglists.py")
convert_test_file("views/test_user_profile.py")
