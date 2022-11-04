from c2corg_api.views import health as health_view
from c2corg_api.views import cooker as cooker_view

from c2corg_api.legacy.views.articles import ArticlesView, ArticleView, ArticleVersionView
from c2corg_api.legacy.views.books import BooksView, BookVersionView, BookView
from c2corg_api.legacy.views.profiles import ProfilesView, ProfileView
from c2corg_api.legacy.views.users import account as account_view
from c2corg_api.legacy.views.users import block as block_view
from c2corg_api.legacy.views.users import unblock as unblock_view
from c2corg_api.legacy.views.users import follow as follow_view
from c2corg_api.legacy.views.users import unfollow as unfollow_view
from c2corg_api.legacy.views.users import login as login_view
from c2corg_api.legacy.views.users import logout as logout_view
from c2corg_api.legacy.views.users import preferences as preferences_view
from c2corg_api.legacy.views.users import request_password_change as request_password_change_view
from c2corg_api.legacy.views.users import register as register_view
from c2corg_api.legacy.views.users import update_preferred_language as update_preferred_language_view
from c2corg_api.legacy.views.users import validate_change_email as validate_change_email_view
from c2corg_api.legacy.views.users import validate_new_password as validate_new_password_view
from c2corg_api.legacy.views.users import validate_register_email as validate_register_email_view


def add_legacy_modules(app, api):

    # define v6 interface
    api.add_modules(app, health_view, cooker_view, url_prefix="")
    api.add_modules(
        app,
        register_view,
        validate_register_email_view,
        validate_change_email_view,
        request_password_change_view,
        validate_new_password_view,
        url_prefix="",
    )
    api.add_modules(
        app,
        login_view,
        logout_view,
        account_view,
        update_preferred_language_view,
        preferences_view,
        follow_view,
        unfollow_view,
        url_prefix="",
    )
    api.add_modules(
        app,
        block_view,
        unblock_view,
        url_prefix="",
    )

    api.add_modules(app, ProfilesView(), ProfileView(), url_prefix="")
    api.add_modules(app, ArticlesView(), ArticleView(), ArticleVersionView(), url_prefix="")
    api.add_modules(app, BooksView(), BookView(), BookVersionView(), url_prefix="")
