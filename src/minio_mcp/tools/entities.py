from dataclasses import dataclass


@dataclass
class TextContent:
    response: dict
    error: str = None
    status_code: int = 200
