from realerikrani.project import *


def test_it_exports_error_classes():
    assert ProjectError
    assert ProjectNotFoundError
    assert ProjectTokenError
    assert ProjectTokenKeyIdInvalidError
    assert ProjectTokenKeyIdNotFoundError
    assert PublicKeyNotFoundError


def test_it_exports_regular_classes():
    assert Project
    assert PublicKey


def test_it_exports_modules():
    assert bearer_extractor
    assert payload_converter
    assert project_repo
    assert project_service


def test_it_exports_registering_function():
    assert register_project
