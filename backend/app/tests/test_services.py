from typing import Any, cast

import pytest
from fastapi import HTTPException, UploadFile

from app.core.security import hash_password, verify_password
from app.utils.document_validator import validate_file


class DummyFile:

    def __init__(self, filename: str):
        self.filename = filename


def test_password_hashing():
    password = "SecretPassword123!"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_document_validator_allowed():
    dummy = cast(UploadFile, cast(Any, DummyFile("legal_contract.pdf")))
    validate_file(dummy)


def test_document_validator_disallowed():
    dummy = cast(UploadFile, cast(Any, DummyFile("malicious_script.exe")))
    with pytest.raises(HTTPException) as exc_info:
        validate_file(dummy)
    assert exc_info.value.status_code == 400
