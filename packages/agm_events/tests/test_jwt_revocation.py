from agm_events.jwt_revocation import (
    apply_token_revoked_payload,
    clear_revocation_cache,
    is_jti_revoked,
    revoke_jti,
)


def setup_function():
    clear_revocation_cache()


def test_revoke_and_check_jti():
    revoke_jti("abc-123")
    assert is_jti_revoked("abc-123")
    assert not is_jti_revoked("other")


def test_apply_token_revoked_payload():
    apply_token_revoked_payload({"jti": "from-event", "user_id": 42})
    assert is_jti_revoked("from-event")
