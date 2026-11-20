"""Lossless, non-executable source storage for editable GDD HTML files."""

from __future__ import annotations

import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


SOURCE_ID = "gdd-source"
SOURCE_PATTERN = re.compile(
    r'<script id="gdd-source" type="application/json">(.*?)</script>\n?', re.S
)


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def data_digest(data: dict[str, Any]) -> str:
    return digest(json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False))


def embed_source(rendered: str, data: dict[str, Any]) -> str:
    if re.search(r'\bid\s*=\s*[\"\']gdd-source[\"\']', rendered, re.I):
        raise ValueError("template already contains gdd-source")
    payload = json.dumps(
        {"format": "game-gdd-html/source-v1", "render_sha256": digest(rendered),
         "source_sha256": data_digest(data), "data": data},
        ensure_ascii=False, separators=(",", ":"), allow_nan=False,
    )
    for char, escaped in (("&", "\\u0026"), ("<", "\\u003c"), (">", "\\u003e"),
                          ("\u2028", "\\u2028"), ("\u2029", "\\u2029")):
        payload = payload.replace(char, escaped)
    match = re.search(r"</body\s*>", rendered, re.I)
    if not match:
        raise ValueError("template must contain a closing body tag")
    block = f'<script id="{SOURCE_ID}" type="application/json">{payload}</script>\n'
    return rendered[:match.start()] + block + rendered[match.start():]


class LegacyDocument(ValueError):
    """A document needs content reconstruction, not a new blank scaffold."""


def check_document(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict) or not isinstance(data.get("document"), dict):
        raise ValueError("source must contain a document object")
    if not isinstance(data.get("sections"), list) or not data["sections"]:
        raise ValueError("source must contain a non-empty sections array")
    ids = [item.get("id") if isinstance(item, dict) else None for item in data["sections"]]
    if any(not isinstance(item, str) or not item for item in ids) or len(set(ids)) != len(ids):
        raise ValueError("source section IDs must be non-empty and unique")
    return data


def load_document(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() == ".json":
        return check_document(json.loads(raw))
    if path.suffix.lower() not in {".html", ".htm"}:
        raise ValueError("use a renderer JSON or HTML source; reconstruct other formats first")
    matches = list(SOURCE_PATTERN.finditer(raw))
    if not matches:
        raise LegacyDocument("HTML has no recoverable embedded source; reconstruct from the original")
    if len(matches) != 1:
        raise ValueError("HTML must contain exactly one embedded source")
    payload = json.loads(matches[0].group(1))
    if not isinstance(payload, dict) or payload.get("format") != "game-gdd-html/source-v1":
        raise ValueError("unsupported embedded source format")
    without_source = raw[:matches[0].start()] + raw[matches[0].end():]
    if digest(without_source) != payload.get("render_sha256"):
        raise LegacyDocument("HTML differs from its embedded source; reconcile visible edits first")
    data = check_document(payload.get("data"))
    if data_digest(data) != payload.get("source_sha256"):
        raise LegacyDocument("Embedded source was edited; reconcile it with the visible document first")
    return data


class ReferenceParser(HTMLParser):
    """Extract readable legacy evidence; never claim to reconstruct full blocks."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.metadata: dict[str, str] = {}
        self.text: list[str] = []
        self.hidden: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "meta" and attributes.get("name", "").startswith("gdd-"):
            self.metadata[str(attributes["name"])] = attributes.get("content") or ""
        if tag in {"script", "style", "nav", "head"}:
            self.hidden.append(tag)
        if not self.hidden and tag in {"p", "h1", "h2", "h3", "tr", "li", "section", "br"}:
            self.text.append("\n")
        if not self.hidden and tag in {"td", "th"}:
            self.text.append(" | ")

    def handle_endtag(self, tag: str) -> None:
        if self.hidden and self.hidden[-1] == tag:
            self.hidden.pop()
        if not self.hidden and tag in {"p", "h1", "h2", "h3", "tr", "li", "section"}:
            self.text.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.hidden:
            self.text.append(data)


def legacy_evidence(path: Path) -> dict[str, Any]:
    parser = ReferenceParser()
    raw = path.read_text(encoding="utf-8-sig")
    parser.feed(raw)
    lines = [re.sub(r"[\t ]+", " ", line).strip() for line in "".join(parser.text).splitlines()]
    return {"source": str(path.resolve()), "sha256": digest(raw), "metadata": parser.metadata,
            "visible_text": "\n".join(line for line in lines if line),
            "limitation": "Reference text only. Inspect original tables, diagrams, charts and layout; this is not a lossless JSON reconstruction."}
