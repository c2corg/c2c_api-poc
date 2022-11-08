import pytest
from c2corg_api.tests.legacy.views import BaseTestRest
from c2corg_api.legacy.views.document_schemas import route_documents_config, topo_map_documents_config


class TestGetDocumentsConfig(BaseTestRest):
    @pytest.mark.skip(reason="Not a test view. It test fields for collection get, which is not used")
    def test_get_load_only_fields_routes(self):
        fields = route_documents_config.get_load_only_fields()
        assert "elevation_max" in fields
        assert "ski_rating" in fields
        assert "rock_free_rating" in fields
        assert "height_diff_access" not in fields
        assert "lift_access" not in fields

        assert "geometry.geom" not in fields
        assert "geom" not in fields

        assert "locales.title" not in fields
        assert "title" not in fields

    @pytest.mark.skip(reason="Not a test view. It test fields for collection get, which is not used")
    def test_get_load_only_fields_locales_routes(self):
        fields = route_documents_config.get_load_only_fields_locales()
        assert "title" in fields
        assert "title_prefix" in fields
        assert "summary" in fields
        assert "description" not in fields
        assert "gear" not in fields

    @pytest.mark.skip(reason="Not a test view. It test fields for collection get, which is not used")
    def test_get_load_only_fields_geometry_routes(self):
        fields = route_documents_config.get_load_only_fields_geometry()
        assert "geom" in fields
        assert "geom_detail" not in fields

    @pytest.mark.skip(reason="Not a test view. It test fields for collection get, which is not used")
    def test_get_load_only_fields_topo_map(self):
        fields = topo_map_documents_config.get_load_only_fields()
        assert "code" in fields
        assert "editor" in fields
        assert "scale" not in fields
        assert "lift_access" not in fields

    @pytest.mark.skip(reason="Not a test view. It test fields for collection get, which is not used")
    def test_get_load_only_fields_locales_topo_map(self):
        fields = topo_map_documents_config.get_load_only_fields_locales()
        assert "title" in fields
        assert "summary" not in fields
        assert "description" not in fields

    @pytest.mark.skip(reason="Not a test view. It test fields for collection get, which is not used")
    def test_get_load_only_fields_geometry_topo_map(self):
        fields = topo_map_documents_config.get_load_only_fields_geometry()
        assert "geom" not in fields
        assert "geom_detail" not in fields
