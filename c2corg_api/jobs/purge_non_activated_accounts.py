import logging
from flask_camp import current_api
from flask_camp.models import User, Document, DocumentVersion
from datetime import datetime, timedelta
from sqlalchemy.sql.expression import and_

from c2corg_api.app import ProfilePageLink
from c2corg_api.models import VALIDATION_EXPIRE_DAYS


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
        rows = session.query(ProfilePageLink.document_id).filter(ProfilePageLink.user_id.in_(user_ids)).all()
        document_ids = [row[0] for row in rows]
        delete(ProfilePageLink, ProfilePageLink.user_id, user_ids)

        Document.query.filter(Document.id.in_(document_ids)).update({"last_version_id": None})
        delete(DocumentVersion, DocumentVersion.document_id, document_ids)
        delete(Document, Document.id, document_ids)
        delete(User, User.id, user_ids)
        session.commit()
