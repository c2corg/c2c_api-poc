from c2corg_api.legacy.models.association import Association


class AreaAssociation(Association):
    def __init__(self, document, area):
        super().__init__(parent_document=document, child_document=area)
