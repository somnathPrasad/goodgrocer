from app.models.domain import AuthSession
from app.services import auth


def test_logout_invalidates_the_session(db, data):
    session = auth.new_session(db, customer_id=data["customer"].id)
    token_hash = auth.digest(session["token"])
    db.flush()

    auth.logout(db, db.get(AuthSession, token_hash))

    assert db.get(AuthSession, token_hash) is None
