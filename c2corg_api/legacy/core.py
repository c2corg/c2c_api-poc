from c2corg_api.views import cooker as cooker_view
from c2corg_api.views import forum as forum_view
from c2corg_api.views import search as search_view
from c2corg_api.views import health as health_view
from c2corg_api.views.sitemap import Sitemaps as SitemapsView

from c2corg_api.legacy.views.articles import ArticlesView, ArticleView, ArticleVersionView
from c2corg_api.legacy.views.books import BooksView, BookVersionView, BookView
from c2corg_api.legacy.views.documents import (
    protect as protect_view,
    unprotect as unprotect_view,
    revert as revert_view,
    merge as merge_view,
    changes as changes_view,
)
from c2corg_api.legacy.views.document_tag import DocumentTagAdd, DocumentTagRemove, DocumentTagHas
from c2corg_api.legacy.views.maps import MapsView, MapVersionView, MapView
from c2corg_api.legacy.views.outings import OutingsView, OutingVersionView, OutingView
from c2corg_api.legacy.views.profiles import ProfilesView, ProfileView
from c2corg_api.legacy.views.routes import RoutesView, RouteView, RouteVersionView
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
from c2corg_api.legacy.views.waypoints import WaypointsView, WaypointView, WaypointVersionView
from c2corg_api.legacy.views.xreports import XreportsView, XreportView, XreportVersionView


def add_legacy_modules(app, api):

    # define v6 interface
    api.add_views(app, health_view, cooker_view, search_view, forum_view, url_prefix="")

    api.add_views(app, protect_view, unprotect_view, revert_view, merge_view, changes_view, url_prefix="")

    api.add_views(
        app,
        register_view,
        validate_register_email_view,
        validate_change_email_view,
        request_password_change_view,
        validate_new_password_view,
        url_prefix="",
    )
    api.add_views(
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
    api.add_views(
        app,
        block_view,
        unblock_view,
        url_prefix="",
    )

    api.add_views(app, ArticlesView(), ArticleView(), ArticleVersionView(), url_prefix="")
    api.add_views(app, BooksView(), BookView(), BookVersionView(), url_prefix="")
    api.add_views(app, MapsView(), MapView(), MapVersionView(), url_prefix="")
    api.add_views(app, OutingsView(), OutingView(), OutingVersionView(), url_prefix="")
    api.add_views(app, ProfilesView(), ProfileView(), url_prefix="")
    api.add_views(app, RoutesView(), RouteView(), RouteVersionView(), url_prefix="")
    api.add_views(app, WaypointsView(), WaypointView(), WaypointVersionView(), url_prefix="")
    api.add_views(app, XreportsView(), XreportView(), XreportVersionView(), url_prefix="")

    api.add_views(app, SitemapsView(), url_prefix="")

    api.add_views(app, DocumentTagAdd(), DocumentTagRemove(), DocumentTagHas(), url_prefix="")
