from dataclasses import dataclass


@dataclass(slots=True)
class ProjectError(Exception):
    message: str = "issue in the project package"


@dataclass(slots=True)
class ProjectNotFoundError(ProjectError):
    message: str = "project missing"
    code: str = "RESOURCE_MISSING"


@dataclass(slots=True)
class PublicKeyNotFoundError(ProjectError):
    message: str = "key missing"
    code: str = "RESOURCE_MISSING"


@dataclass(slots=True)
class PublicKeyDuplicateError(ProjectError):
    message: str = "public key is already registered"
    code: str = "RESOURCE_ALREADY_EXISTING"


@dataclass(slots=True)
class PublicKeyInvalidError(ProjectError):
    message: str = "public_key must be in RSA PEM format"
    code: str = "VALUE_INVALID"


@dataclass(slots=True)
class ProjectNameError(ProjectError):
    message: str = "project name must be 1..100 characters"
    code: str = "VALUE_INVALID"


@dataclass(slots=True)
class ProjectTokenError(ProjectError): ...


@dataclass(slots=True)
class ProjectTokenKeyIdNotFoundError(ProjectError): ...


@dataclass(slots=True)
class ProjectTokenKeyIdInvalidError(ProjectError): ...
