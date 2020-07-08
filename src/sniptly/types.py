from typing import List, Dict, TypedDict


class Snippet(TypedDict):
    prefix: str
    body: List[str]
    description: str


Snippets = Dict[str, Snippet]
