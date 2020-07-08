from typing import Any
from click import echo, style


def out(message: str, new_line: bool = True, **styles: Any) -> None:
    if "bold" not in styles:
        styles["bold"] = True
        message = style(message, **styles)
    echo(message, nl=new_line)


def err(message: str, new_line: bool = True, **styles: Any) -> None:
    if "fg" not in styles:
        styles["fg"] = "red"
        message = style(message, **styles)
    echo(message, nl=new_line)
