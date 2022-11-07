import logging
from flask_camp import current_api
from flask_camp.models import User, Document, DocumentVersion
from datetime import datetime, timedelta
from sqlalchemy.sql.expression import and_

from c2corg_api.search import DocumentSearch


VALIDATION_EXPIRE_DAYS = 3

log = logging.getLogger(__name__)


def purge_account():
    now = datetime.utcnow()

    session = current_api.database.session

    def delete(cls, attr, ids):
        session.query(cls).filter(attr.in_(ids)).delete(synchronize_session=False)

    rows = (
        session.query(User.id)
        .filter(
            and_(
                User._email.is_(None),
                User.creation_date < now - timedelta(days=VALIDATION_EXPIRE_DAYS),  # TODO
            )
        )
        .all()
    )
    user_ids = [row[0] for row in rows]

    log.info("Deleting %d non activated users: %s", len(user_ids), user_ids)

    if len(user_ids) > 0:
        rows = session.query(DocumentSearch.id).filter(DocumentSearch.user_id.in_(user_ids)).all()
        document_ids = [row[0] for row in rows]
        delete(DocumentSearch, DocumentSearch.user_id, user_ids)

        Document.query.filter(Document.id.in_(document_ids)).update({"last_version_id": None})
        delete(DocumentVersion, DocumentVersion.document_id, document_ids)
        delete(Document, Document.id, document_ids)
        delete(User, User.id, user_ids)
        session.commit()
