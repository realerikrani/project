from typing import Any

from realerikrani import base64token


def to_page_size(data: dict) -> int | None:
    try:
        return int(data["page_size"])
    except (ValueError, KeyError):
        return None


def to_page_size_and_data(data: dict) -> tuple[int, list[tuple[str, Any]]] | None:
    try:
        return int(data["page_size"]), []
    except (ValueError, KeyError):
        try:
            page_token = data["page_token"]
        except KeyError:
            return None

        if (page_token := base64token.decode(page_token)) is None:
            return None

        if len(page_token) == 1:
            return None

        try:
            page_size = int(page_token["page_size"])
        except (ValueError, KeyError):
            return None
        else:
            return page_size, [
                (k, v) for k, v in page_token.items() if k != "page_size"
            ]
