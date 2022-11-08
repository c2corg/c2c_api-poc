from c2corg_api.legacy.models.association import Association


class TopoMapAssociation(Association):
    def __init__(self, document, topo_map):
        super().__init__(parent_document=document, child_document=topo_map)
