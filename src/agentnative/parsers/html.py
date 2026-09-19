from __future__ import annotations

import json
from html.parser import HTMLParser
from typing import Any


class _SurfaceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.links: list[str] = []
        self.metas: list[dict[str, str]] = []
        self.json_ld: list[dict[str, Any]] = []
        self._in_title = False
        self._script_type = ""
        self._script_buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag.lower() == "title":
            self._in_title = True
        elif tag.lower() == "a" and values.get("href"):
            self.links.append(values["href"])
        elif tag.lower() == "link" and values.get("href"):
            self.links.append(values["href"])
        elif tag.lower() == "meta":
            key = values.get("name") or values.get("property") or values.get("itemprop")
            if key and values.get("content"):
                self.metas.append({"name": key, "content": values["content"]})
        elif tag.lower() == "script":
            self._script_type = values.get("type", "").lower()
            self._script_buffer = []

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False
        elif tag.lower() == "script":
            if self._script_type == "application/ld+json":
                try:
                    parsed = json.loads("".join(self._script_buffer))
                    if isinstance(parsed, dict):
                        self.json_ld.append(parsed)
                    elif isinstance(parsed, list):
                        self.json_ld.extend(item for item in parsed if isinstance(item, dict))
                except json.JSONDecodeError:
                    pass
            self._script_type = ""
            self._script_buffer = []

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
        if self._script_type:
            self._script_buffer.append(data)


def parse_html(content: str) -> dict[str, Any]:
    parser = _SurfaceParser()
    parser.feed(content)
    parser.close()
    return {
        "title": parser.title.strip(),
        "links": parser.links,
        "metas": parser.metas,
        "json_ld": parser.json_ld,
    }
