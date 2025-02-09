import pytest
from flask import Flask
from werkzeug.datastructures import Headers

from realerikrani.flaskapierr import ErrorGroup
from realerikrani.project.app import register_project
from realerikrani.project.bearer_extractor import get_bearer

_EXPECTED_BEARER_PARTS_COUNT = 2


@pytest.fixture
def app():
    app = register_project(Flask(__name__))
    app.testing = True
    return app


def test_it_raises_error_for_missing_authorization_header(app: Flask):
    # when
    try:
        with app.test_request_context():
            get_bearer()

    # then
    except ErrorGroup as error:
        assert error.message == "401"
        assert len(error.exceptions) == 1
        assert error.exceptions[0].code == "AUTH_HEADER_MISSING"
        assert error.exceptions[0].message
    else:
        pytest.fail(f"expected {ErrorGroup.__name__}")


@pytest.mark.parametrize("auth_header", ["", "Bearer", "Bearer 1 2"])
def test_it_raises_error_for_non_2_part_authorization_header(
    app: Flask, auth_header: str
):
    # given
    headers = Headers({"Authorization": auth_header})

    # when
    try:
        with app.test_request_context(headers=headers):
            get_bearer()

    # then
    except ErrorGroup as error:
        assert error.message == "401"
        assert len(error.exceptions) == 1
        assert error.exceptions[0].code == "AUTH_HEADER_INVALID"
        assert error.exceptions[0].message
    else:
        pytest.fail(f"expected {ErrorGroup.__name__}")


def test_it_raises_error_for_missing_bearer_in_authorization_header(app: Flask):
    # given
    headers = Headers({"Authorization": "Anything anything"})

    # when
    try:
        with app.test_request_context(headers=headers):
            get_bearer()

    # then
    except ErrorGroup as error:
        assert error.message == "401"
        assert len(error.exceptions) == _EXPECTED_BEARER_PARTS_COUNT
        assert error.exceptions[0].code == "BEARER_MISSING"
        assert error.exceptions[0].message
        assert error.exceptions[1].code == "BEARER_MISSING"
        assert error.exceptions[1].message
    else:
        pytest.fail(f"expected {ErrorGroup.__name__}")


def test_it_returns_bearer_from_authorization_header(app: Flask):
    # given
    bearer_value = "header.payload.signature"
    headers = Headers({"Authorization": f"Bearer {bearer_value}"})

    # when
    with app.test_request_context(headers=headers):
        result = get_bearer()

    # then
    assert result == bearer_value
