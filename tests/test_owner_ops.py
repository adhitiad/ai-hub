import pytest
from fastapi import HTTPException
from src.api.owner_ops import verify_owner
from src.api.roles import UserRole

def test_verify_owner_success():
    """Test verify_owner when the user has OWNER role."""
    user = {"email": "owner@example.com", "role": UserRole.OWNER}
    result = verify_owner(user)
    assert result == user


def test_verify_owner_forbidden():
    """Test verify_owner when the user does not have OWNER role."""
    user = {"email": "admin@example.com", "role": UserRole.ADMIN}
    with pytest.raises(HTTPException) as exc_info:
        verify_owner(user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "OWNER ONLY"
