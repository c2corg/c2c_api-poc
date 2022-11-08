class FilterArea:
    ...


class FollowedUser:
    ...


class DocumentChange:
    def __init__(
        self,
        time,
        user_id,
        change_type,
        document_id,
        document_type,
        user_ids,
        langs,
    ):
        self.time = time
        self.user_id = user_id
        self.change_type = change_type
        self.document_id = document_id
        self.document_type = document_type
        self.user_ids = user_ids
        self.langs = langs

    def propagate_in_documents(self):
        ...  # TODO