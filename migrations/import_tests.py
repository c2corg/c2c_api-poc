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
    dict_member = r"(?:\.|\w)+(?:\[(?:\"\w+\"|\d+)\])+"
    simple_value = r"[^,\n\]\[]+"
    string_list = r'\["\w+"(?:, "\w+")*\]'
    function_call = r"[^\n(]+\([^\n)]*\)"
    litteral_list = r"\[\w+\]"

    return f"({dict_member}|{simple_value}|{string_list}|{function_call}|{litteral_list})"


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


def _legacy_model_replacements():
    return [
        (r"from c2corg_api.models.area ", "from c2corg_api.legacy.models.area "),
        (r"from c2corg_api.models.area_association ", "from c2corg_api.legacy.models.area_association "),
        (r"from c2corg_api.models.article ", "from c2corg_api.legacy.models.article "),
        (r"from c2corg_api.models.association ", "from c2corg_api.legacy.models.association "),
        (r"from c2corg_api.models.cache_version ", "from c2corg_api.legacy.models.cache_version "),
        (r"from c2corg_api.models.book ", "from c2corg_api.legacy.models.book "),
        (r"from c2corg_api.models.common.document_types ", "from c2corg_api.models._core "),
        (r"from c2corg_api.models.document ", "from c2corg_api.legacy.models.document "),
        (r"from c2corg_api.models.document_history ", "from c2corg_api.legacy.models.document_history "),
        (r"from c2corg_api.models.document_topic ", "from c2corg_api.legacy.models.document_topic "),
        (r"from c2corg_api.models.document_tag ", "from c2corg_api.legacy.models.document_tag "),
        (r"from c2corg_api.models.feed ", "from c2corg_api.legacy.models.feed "),
        (r"from c2corg_api.models.image ", "from c2corg_api.legacy.models.image "),
        (r"from c2corg_api.models.mailinglist ", "from c2corg_api.legacy.models.mailinglist "),
        (r"from c2corg_api.models.outing ", "from c2corg_api.legacy.models.outing "),
        (r"from c2corg_api.models.route ", "from c2corg_api.legacy.models.route "),
        (r"from c2corg_api.models.topo_map ", "from c2corg_api.legacy.models.topo_map "),
        (r"from c2corg_api.models.topo_map_association ", "from c2corg_api.legacy.models.topo_map_association "),
        (r"from c2corg_api.models.user_profile ", "from c2corg_api.legacy.models.user_profile "),
        (r"from c2corg_api.models.waypoint ", "from c2corg_api.legacy.models.waypoint "),
        (r"from c2corg_api.models.xreport ", "from c2corg_api.legacy.models.xreport "),
        (r"from c2corg_api.tests.views.test_feed import ", "from c2corg_api.tests.legacy.views.test_feed import "),
        (r"from c2corg_api.views.document_schemas ", "from c2corg_api.legacy.views.document_schemas "),
        (r"from c2corg_api.views.document_tag ", "from c2corg_api.legacy.views.document_tag "),
        (r"from c2corg_api.views.validation ", "from c2corg_api.legacy.views.validation "),
        (r"from c2corg_api.tests ", "from c2corg_api.tests.legacy "),
    ]


replacements = (
    [
        (r"(from c2corg_api.models.sso .*\n)", "# \1\n"),
        (r"(from c2corg_api.views.sso .*\n)", "# \1\n"),
        (r"from cornice.errors import Errors\n", ""),
        (r"# package\n*", ""),
        (r"# -\*- coding: utf-8 -\*-\n", ""),
        # remove useless lines
        (r"    def setUp\(self\):.*\n +super\(\w+, self\)\.setUp\(\)\n\n.   def", "\n    def"),
        (r"(    def setUp\(self\):.*\n +)super\(\w+, self\)\.setUp\(\)\n", r"\1super().setUp()\n"),
        # not very pythonic
        (r"self\.assertTrue\((initial_encoded_password) != (modified_encoded_password)\)", r"assert \1 != \2"),
        (r'self\.assertTrue\(("\w+") in (\w+)\)', r"assert \1 in \2"),
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
        (r"self\.app\.get\((.*)\)(\.json|)\n", r"self.get(\1)\2\n"),
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
        (
            r"from c2corg_api\.models\.user ",
            "from flask_camp.models import User as NewUser\nfrom c2corg_api.legacy.models.user ",
        ),
        (r"from c2corg_api.scripts.es.sync ", "from c2corg_api.legacy.scripts.es.sync "),
        (r"from c2corg_api.scripts.es.fill_index ", "from c2corg_api.legacy.scripts.es.fill_index "),
        (r"from c2corg_api.search ", "from c2corg_api.legacy.search "),
    ]
    + _legacy_model_replacements()
    + [
        (r"from c2corg_api.views.user_follow import", "from c2corg_api.legacy.views.user_follow import"),
        (
            r"from c2corg_api.tests.views import BaseTestRest\n",
            "from c2corg_api.tests.legacy.views import BaseTestRest\n",
        ),
        (r"from c2corg_api.tests.views.test_user", "from c2corg_api.tests.legacy.views.test_user"),
        (
            r"from c2corg_api.search.mappings.user_mapping import SearchUser",
            "from c2corg_api.legacy.search import SearchUser",
        ),
        (r"from c2corg_api.views.document import", "from c2corg_api.legacy.views.document import"),
        (
            r"from c2corg_api.tests.views import BaseDocumentTestRest\n",
            "from c2corg_api.tests.legacy.views import BaseDocumentTestRest\n",
        ),
        (r"from c2corg_api.caching ", "from c2corg_api.legacy.caching "),
        # for now, comment these imports
        (r"(from c2corg_api.models.token.*\n)", r"# \1"),
        (r"(from c2corg_api.models.common.attributes import mailinglists\n)", r"# \1"),
        (r"(from dogpile.cache.api import NO_VALUE\n)", r"# \1"),
        (
            r"from c2corg_api.tests.search import ",
            r"from c2corg_api.tests.legacy.search import ",
        ),
        # targeted replace
        ("username with spaces", "username_with_spaces"),
        ('"forum_username": "Spaceman",', '"forum_username": "username_with_spaces",'),
        ('"forum_username": "Foo",', '"forum_username": "contributor",'),
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
            r'assert json\["errors"\]\[0\]\["description"\] == "Invalid email address"',
            "assert json[\"description\"] == \"'some_useratcamptocamp.org' is not a 'email' on instance ['user']['email']\"",
        ),
        (
            r"self.([\w\d]+)_version = \(\n *self.session.query\(DocumentVersion\)\n *.filter\(DocumentVersion.document_id == self.([\w\d]+).document_id\)\n *.filter\(DocumentVersion.lang == \"en\"\)\n *.first\(\)\n *\)",
            r"self.\1_version = self.session_query_first(DocumentVersion, document_id = self.\2.document_id)\n",
        ),
        (
            r'self\.assertEqual\(errors\[0\]\["description"\], "Invalid geometry type\. Expected: \[\'POINT\'\]\. Got: LINESTRING\."\)',
            r'assert (errors == "\'LineString\' is not one of [\'Point\'] on instance [\'geometry\'][\'geom\'][\'type\']")',
        ),
        (r"(# version with lang 'en'\n *version_en = profile\.versions)\[2\]", r"\1[1]"),
        (r"self\.assertCorniceNotInEnum\(errors\[0\], key\)", "assert key in errors, key"),
        (
            r"self\.app\.app\.registry\.anonymous_user_id =",
            'self.app.config["ANONYMOUS_USER_ID"] =',
        ),
        (r'assert 1 == errors\[0\]\.get\("topic_id"\)\n', ""),
        (r"/sitemaps/r/", "/sitemaps/route/"),
        (r"/sitemaps/w/", "/sitemaps/waypoint/"),
        (r'"/r/(\d)"', r'"/route/\1"'),
        (r'"/w/(\d)"', r'"/waypoint/\1"'),
        (r'"/r/(\d)\.xml"', r'"/route/\1.xml"'),
        (r'"/w/(\d)\.xml"', r'"/waypoint/\1.xml"'),
        (r'"/a/-123", status=400', '"/area/-123", status=404'),
        (r'"/a/-123.xml", status=400', '"/area/-123.xml", status=404'),
        (r'(errors = response.json\["errors"\])\n( *)(self.assertError\(errors, "i", "invalid i"\))', r"# \1\n\2# \3"),
        (
            r'(errors = response.json\["errors"\])\n( *)(self.assertError\(errors, "doc_type", "invalid doc_type"\))',
            r'errors = response.json["description"]\n\2assert "Invalid document type" in errors',
        ),
        (
            r'(locales=\[RouteLocale\(lang="fr", title="Mont Blanc du ciel", title_prefix="Mont Blanc"\)\],\n)',
            r"            main_waypoint_id=self.waypoint2.document_id,\n\1",
        ),
        (
            r"(\w+) = response.xml\n",
            r"from xml.etree import ElementTree\n        \1 = ElementTree.fromstring(response.data)\n",
        ),
        (
            r'routes = body\["routes"\]\n {8}assert 0 == routes\["total"\]',
            r'routes = body["routes"]\n        # assert 0 == routes["total"]',
        ),
        (r'"\{\}/(waypoint|route)s/\{\}/fr/', r'"{}/\1/{}/fr/'),
        # commit after adding test data, as tst session is not query session
        (r"        self._add_test_data\(\)\n", "        self._add_test_data()\n        self.session.commit()\n"),
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
        (
            r' *search_doc = self._check_es_index\(\)\n *assert search_doc\["title_es\"] == "Contributor contributor"',
            "",
        ),
        (r" *self._check_es_index\(\)\n", ""),
        # error messages
        ('"This username already exists"', '"A user still exists with this name"'),
        ('"Already used forum name"', '"Name or email already exists"'),
        (r' *assert len\(body\["errors"\]\) == \d\n', ""),  # error model is different
        (r" *assert len\(errors\) == 1\n", ""),  # error model is different
        (r'assert body\["errors"\]\[0\]\["name"\]', 'assert body["name"]'),
        (r'json\["errors"\]\[0\]\["description"\]', 'json["description"]'),
    ]
)

skipped_methods_by_file = {
    "views/test_user.py": {
        "test_purge_tokens": "No such model in flask_camp",
        "test_renew_success": "/renew is not used",
        "test_renew_token_different_success": "/renew is not used",
        "test_login_blocked_account": "blocked users can log-in",
        "test_login_discourse_success": "sso in login payload not used anymore?",
        "test_register_username_email_not_equals_email": "username is removed in new model",
    },
    "views/test_user_account.py": {
        "test_read_account_info_blocked_account": "blocked users can view their account",
    },
    "views/test_user_preferences.py": {
        "test_post_preferences_invalid": "Too painful to automatically import, recoded it",
        "test_post_preferences": "Too painful to automatically import, recoded it",
    },
    "views/test_user_profile.py": {
        "test_get_collection_paginated": "TODO should be working",
        "test_get_unauthenticated_private_profile": "useless feature: anybody can create a profile to see profile",
        "test_get_caching": "caching is handled and tested in flask-camp",
        "test_get_info": "test_get_info is not used in UI",
        "test_put_wrong_locale_version": "Locales are not versionned in the new model",
    },
    "views/test_article.py": {
        "test_get_version_caching": "caching is handled and tested in flask-camp",
        "test_get_caching": "caching is handled and tested in flask-camp",
        "test_get_info": "test_get_info is not used in UI",
        "test_get_info_best_lang": "test_get_info is not used in UI",
        "test_get_info_404": "test_get_info is not used in UI",
        "test_post_error": "useless test: empty payload...",
        "test_post_success": "Rewritted without the part on associations, as it does not exists in the mew model",
        "test_put_wrong_locale_version": "Locales are not versionned in the new model",
        "test_put_success_all": "Rewritted without the part on associations, as it does not exists in the mew model",
        "test_get_associations_history": "This view is not relevant in new model",
    },
    "views/test_book.py": {
        "test_get_version_caching": "caching is handled and tested in flask-camp",
        "test_get_caching": "caching is handled and tested in flask-camp",
        "test_get_info": "test_get_info is not used in UI",
        "test_get_info_best_lang": "test_get_info is not used in UI",
        "test_get_info_404": "test_get_info is not used in UI",
        "test_post_error": "useless test: empty payload...",
        "test_post_success": "Rewritted without the part on associations, as it does not exists in the mew model",
        "test_put_wrong_locale_version": "Locales are not versionned in the new model",
        "test_put_success_all": "Rewritted without the part on associations, as it does not exists in the mew model",
        "test_get_associations_history": "This view is not relevant in new model",
    },
    "views/test_xreport.py": {
        "test_get_version_caching": "caching is handled and tested in flask-camp",
        "test_get_caching": "caching is handled and tested in flask-camp",
        "test_get_info": "test_get_info is not used in UI",
        "test_get_info_best_lang": "test_get_info is not used in UI",
        "test_get_info_404": "test_get_info is not used in UI",
        "test_get_associations_history": "This view is not relevant in new model",
        "test_post_error": "useless test: empty payload...",
        "test_put_wrong_locale_version": "Locales are not versionned in the new model",
        "test_post_success": "Rewritted without the part on associations, as it does not exists in the mew model",
        "test_put_success_all": "Rewritted without the part on associations, as it does not exists in the mew model",
    },
    "views/test_topo_map.py": {
        "test_get_caching": "caching is handled and tested in flask-camp",
        "test_get_info": "test_get_info is not used in UI",
        "test_put_wrong_locale_version": "Locales are not versionned in the new model",
        "test_post_error": "useless test: empty payload...",
        "test_post_success": "Rewritted without the part on associations, as it does not exists in the mew model",
        "test_put_success_all": "Rewritted without the part on associations, as it does not exists in the mew model",
    },
    "views/test_langs.py": {
        "test_feed": "feed will probably be replaced by recent outings",
    },
    "views/test_document_revert.py": {
        "test_revert_latest_version_id": "PITA, rewritted",
        "test_revert_waypoint": "PITA, rewritted",
        "test_revert_route": "PITA, rewritted",
    },
    "views/test_document_schema.py": {
        "test_get_load_only_fields_routes": "Not a test view. It test fields for collection get, which is not used",
        "test_get_load_only_fields_locales_routes": "Not a test view. It test fields for collection get, which is not used",
        "test_get_load_only_fields_geometry_routes": "Not a test view. It test fields for collection get, which is not used",
        "test_get_load_only_fields_topo_map": "Not a test view. It test fields for collection get, which is not used",
        "test_get_load_only_fields_locales_topo_map": "Not a test view. It test fields for collection get, which is not used",
        "test_get_load_only_fields_geometry_topo_map": "Not a test view. It test fields for collection get, which is not used",
    },
    "views/test_document_merge.py": {
        "test_already_merged": "setup did not commit the data, preventing the test to success in flask-sqlalchemy model",
        "test_merge_waypoint": "PITA, rewritted",
        "test_merge_image": "Nothing to test, old images must not be deleted",
        "test_merge_image_error_deleting_files": "Nothing to test, old images must not be deleted",
        "test_tags": "PITA, rewritted",
    },
    "views/test_forum.py": {
        "test_post_success": "PITA, rewritted",
        "test_post_without_title": "PITA, rewritted",
    },
    "views/test_document_tag.py": {
        "test_untag_not_tagged": "It's idempotent, don't test",
        "test_tag": "PITA, rewritted",
        "test_untag": "PITA, rewritted",
    },
    "views/test_sitemap.py": {"test_get_waypoint_sitemap_no_pages": "Simple 200 with empty response"},
    "views/test_sitemap_xml.py": {"test_get_waypoint_sitemap_no_pages": "Simple 200 with empty response"},
    "views/test_search.py": {"test_search_by_document_id": "Not used by the API"},
    "views/test_area.py": {
        "test_get_caching": "caching is handled and tested in flask-camp",
        "test_get_info": "test_get_info is not used in UI",
        "test_post_error": "useless test: empty payload...",
        "test_put_wrong_locale_version": "Locales are not versionned in the new model",
        "test_get_associations_history": "This view is not relevant in new model",
        "test_post_success": "Association is not automatically computed in the new model",
        "test_put_success_all_as_moderator": "Association is not automatically computed in the new model",
        "test_put_success_figures_only": "Association is not automatically computed in the new model",
        "test_put_success_lang_only": "Association is not automatically computed in the new model",
        "test_put_update_geometry_fail": "error nmodel is not the same, rewritted",
    },
    "views/test_outing.py": {
        "test_get_version_caching": "caching is handled and tested in flask-camp",
        "test_get_caching": "caching is handled and tested in flask-camp",
        "test_get_info": "test_get_info is not used in UI",
        "test_get_info_best_lang": "test_get_info is not used in UI",
        "test_get_info_404": "test_get_info is not used in UI",
        "test_get_associations_history": "This view is not relevant in new model",
        "test_post_error": "useless test: empty payload...",
        "test_put_wrong_locale_version": "Locales are not versionned in the new model",
    },
    "views/test_route.py": {
        "test_get_version_caching": "caching is handled and tested in flask-camp",
        "test_get_caching": "caching is handled and tested in flask-camp",
        "test_get_info": "test_get_info is not used in UI",
        "test_get_info_best_lang": "test_get_info is not used in UI",
        "test_get_info_404": "test_get_info is not used in UI",
        "test_get_associations_history": "This view is not relevant in new model",
        "test_post_error": "useless test: empty payload...",
        "test_put_wrong_locale_version": "Locales are not versionned in the new model",
    },
    "views/test_waypoint.py": {
        "test_get_version_caching": "caching is handled and tested in flask-camp",
        "test_get_caching": "caching is handled and tested in flask-camp",
        "test_get_info": "test_get_info is not used in UI",
        "test_get_info_best_lang": "test_get_info is not used in UI",
        "test_get_info_404": "test_get_info is not used in UI",
        "test_get_associations_history": "This view is not relevant in new model",
        "test_post_error": "useless test: empty payload...",
        "test_put_wrong_locale_version": "Locales are not versionned in the new model",
    },
    "views/test_image.py": {
        "test_get_version_caching": "caching is handled and tested in flask-camp",
        "test_get_caching": "caching is handled and tested in flask-camp",
        "test_get_info": "test_get_info is not used in UI",
        "test_get_info_best_lang": "test_get_info is not used in UI",
        "test_get_info_404": "test_get_info is not used in UI",
        "test_get_associations_history": "This view is not relevant in new model",
        "test_post_error": "useless test: empty payload...",
        "test_put_wrong_locale_version": "Locales are not versionned in the new model",
    },
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

skipped_modules = {
    "views/test_document_changes.py": "on new model, all changes are presnets, aven on outings",
    "views/test_feed.py": "Will probably no ported",
    "views/test_validation.py": "Not a views test",
    "views/test_sso.py": "not used anymore",
    "views/test_association.py": "Associations are handled totally differently",
}


def convert_test_file(filename, make_replacements=True):

    code = get_code(filename)

    if make_replacements:
        for pattern, new_value in replacements:
            code = re.sub(pattern, new_value, code)

        skipped_methods = skipped_methods_by_file.get(filename, {})
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

        code = code.strip()

        # remove empty init file
        if filename.endswith("__init__.py"):
            if len(code) == 0:
                return

        if filename in skipped_modules:
            code = f"import pytest\n\npytestmark = pytest.mark.skip({repr(skipped_modules[filename])})\n{code}"
        else:
            code = f"import pytest\n{code}"

        code = black.format_str(code, mode=black.Mode(line_length=120))

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


# convert_test_folder("markdown")   # ok


convert_test_file("views/test_area.py")  ######################  20K
convert_test_file("views/test_article.py")  ###################  25K
convert_test_file("views/test_association.py")  ###############  29K
convert_test_file("views/test_book.py")  ######################  21K
convert_test_file("views/test_cooker.py")  ####################  606
convert_test_file("views/test_document_changes.py")  ########## 6.2K
# convert_test_file("views/test_document_delete.py")  #########  38K
convert_test_file("views/test_document_merge.py")  ############  13K
convert_test_file("views/test_document_protect.py")  ########## 4.7K
convert_test_file("views/test_document_revert.py")  ###########  12K
convert_test_file("views/test_document_schema.py")  ########### 2.1K
convert_test_file("views/test_document_tag.py")  ############## 4.9K
convert_test_file("views/test_feed.py")  ######################  21K
convert_test_file("views/test_forum.py")  ##################### 6.6K
convert_test_file("views/test_health.py")  ####################  345
convert_test_file("views/test_image.py")  #####################  40K
convert_test_file("views/test_langs.py")  ##################### 4.8K
convert_test_file("views/test_outing.py")  ####################  54K
convert_test_file("views/test_route.py")  #####################  50K
convert_test_file("views/test_search.py")  #################### 7.0K
convert_test_file("views/test_sitemap.py")  ################### 3.1K
convert_test_file("views/test_sitemap_xml.py")  ############### 3.6K
convert_test_file("views/test_sso.py")  #######################  15K
convert_test_file("views/test_topo_map.py")  ##################  16K
convert_test_file("views/test_user.py")  ######################  24K
convert_test_file("views/test_user_account.py")  ############## 6.7K
convert_test_file("views/test_user_block.py")  ################ 8.4K
convert_test_file("views/test_user_follow.py")  ############### 6.7K
convert_test_file("views/test_user_mailinglists.py")  ######### 3.0K
convert_test_file("views/test_user_preferences.py")  ########## 4.7K
convert_test_file("views/test_user_profile.py")  ##############  15K
convert_test_file("views/test_validation.py")  ################ 6.1K
convert_test_file("views/test_waypoint.py")  ##################  63K
convert_test_file("views/test_xreport.py")  ###################  34K
