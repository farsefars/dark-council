"""Small, dependency-free Markdown renderer for the Dark Council rulebooks."""

from __future__ import annotations

from dataclasses import dataclass
import html
import re
from typing import Iterable


TOP_SECTION_RE = re.compile(r"^#{1,2}\s+(\d+)\.\s+(.+?)\s*$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
TABLE_DIVIDER_RE = re.compile(r"^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*$")
LIST_RE = re.compile(r"^(\s*)([-*+]|\d+\.)\s+(.+)$")


@dataclass(frozen=True)
class Section:
    number: int
    title: str
    heading_level: int
    body: str


def split_sections(markdown: str) -> tuple[str, list[Section]]:
    """Split a rulebook into its preface and numbered top-level sections."""
    lines = markdown.splitlines()
    starts: list[tuple[int, re.Match[str]]] = []
    for index, line in enumerate(lines):
        match = TOP_SECTION_RE.match(line)
        if match:
            starts.append((index, match))

    if not starts:
        raise ValueError("No numbered top-level sections found")

    preface = "\n".join(lines[: starts[0][0]]).strip()
    sections: list[Section] = []
    for position, (start, match) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        sections.append(
            Section(
                number=int(match.group(1)),
                title=match.group(2).strip(),
                heading_level=len(lines[start].split(" ", 1)[0]),
                body="\n".join(lines[start + 1 : end]).strip(),
            )
        )
    return preface, sections


def _slug(text: str) -> str:
    value = re.sub(r"<[^>]+>", "", text).lower()
    value = re.sub(r"[^\w\u0400-\u04ff]+", "-", value, flags=re.UNICODE).strip("-")
    return value or "section"


def _inline(text: str) -> str:
    escaped = html.escape(text, quote=False)
    code_tokens: list[str] = []

    def store_code(match: re.Match[str]) -> str:
        code_tokens.append(f"<code>{html.escape(match.group(1))}</code>")
        return f"\x00CODE{len(code_tokens) - 1}\x00"

    escaped = re.sub(r"`([^`]+)`", store_code, escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", escaped)
    escaped = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: f'<a href="{html.escape(m.group(2), quote=True)}">{m.group(1)}</a>',
        escaped,
    )
    for index, token in enumerate(code_tokens):
        escaped = escaped.replace(f"\x00CODE{index}\x00", token)
    return escaped


def _table(lines: list[str]) -> str:
    rows = [[cell.strip() for cell in line.strip().strip("|").split("|")] for line in lines]
    header = rows[0]
    body = rows[2:]
    output = ['<div class="table-scroll"><table><thead><tr>']
    output.extend(f"<th>{_inline(cell)}</th>" for cell in header)
    output.append("</tr></thead><tbody>")
    for row in body:
        output.append("<tr>")
        output.extend(f"<td>{_inline(cell)}</td>" for cell in row)
        output.append("</tr>")
    output.append("</tbody></table></div>")
    return "".join(output)


def _blockquote(lines: list[str]) -> str:
    content = [re.sub(r"^\s*>\s?", "", line) for line in lines]
    return f"<blockquote>{render_markdown(chr(10).join(content))}</blockquote>"


def _consume_list(lines: list[str], start: int, base_indent: int) -> tuple[str, int]:
    first = LIST_RE.match(lines[start])
    if not first:
        raise ValueError("List parser called on a non-list line")
    ordered = first.group(2).endswith(".")
    tag = "ol" if ordered else "ul"
    items: list[str] = []
    index = start

    while index < len(lines):
        current = LIST_RE.match(lines[index])
        if not current or len(current.group(1)) != base_indent:
            break
        if current.group(2).endswith(".") != ordered:
            break

        text = current.group(3).strip()
        index += 1
        continuations: list[str] = []
        nested: list[str] = []
        while index < len(lines):
            next_line = lines[index]
            if not next_line.strip():
                break
            next_item = LIST_RE.match(next_line)
            next_indent = len(next_line) - len(next_line.lstrip())
            if next_item and len(next_item.group(1)) == base_indent:
                break
            if next_item and len(next_item.group(1)) > base_indent:
                nested_html, index = _consume_list(lines, index, len(next_item.group(1)))
                nested.append(nested_html)
                continue
            if next_indent > base_indent:
                continuations.append(next_line.strip())
                index += 1
                continue
            break

        task = re.match(r"^\[([ xX])\]\s+(.+)$", text)
        if task:
            checked = " checked" if task.group(1).lower() == "x" else ""
            item_html = (
                f'<label class="task-item"><input type="checkbox" disabled{checked}>'
                f"{_inline(task.group(2))}</label>"
            )
        else:
            item_html = _inline(" ".join([text, *continuations]))
        items.append(f"<li>{item_html}{''.join(nested)}</li>")

    return f"<{tag}>{''.join(items)}</{tag}>", index


def render_markdown(markdown: str, *, id_prefix: str = "") -> str:
    """Render the project Markdown subset to accessible HTML."""
    lines = markdown.splitlines()
    output: list[str] = []
    paragraph: list[str] = []
    index = 0

    def flush_paragraph() -> None:
        if not paragraph:
            return
        text = " ".join(part.strip() for part in paragraph)
        css = ' class="syndicate-aside"' if text.startswith("▶") else ""
        output.append(f"<p{css}>{_inline(text)}</p>")
        paragraph.clear()

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            index += 1
            continue

        heading = HEADING_RE.match(line)
        if heading:
            flush_paragraph()
            level = min(len(heading.group(1)) + 1, 6)
            title = heading.group(2).strip()
            ident = f"{id_prefix}{_slug(title)}"
            output.append(f'<h{level} id="{ident}">{_inline(title)}</h{level}>')
            index += 1
            continue

        if stripped in {"---", "***", "___"}:
            flush_paragraph()
            output.append("<hr>")
            index += 1
            continue

        if stripped.startswith(">"):
            flush_paragraph()
            block: list[str] = []
            while index < len(lines) and (lines[index].strip().startswith(">") or not lines[index].strip()):
                block.append(lines[index])
                index += 1
            output.append(_blockquote(block))
            continue

        if "|" in stripped and index + 1 < len(lines) and TABLE_DIVIDER_RE.match(lines[index + 1]):
            flush_paragraph()
            table_lines = [line, lines[index + 1]]
            index += 2
            while index < len(lines) and "|" in lines[index] and lines[index].strip():
                table_lines.append(lines[index])
                index += 1
            output.append(_table(table_lines))
            continue

        list_match = LIST_RE.match(line)
        if list_match:
            flush_paragraph()
            base_indent = len(list_match.group(1))
            list_html, index = _consume_list(lines, index, base_indent)
            output.append(list_html)
            continue

        paragraph.append(line)
        index += 1

    flush_paragraph()
    return "\n".join(output)


def render_section(section: Section, *, language: str) -> str:
    ident = f"{language}-section-{section.number}"
    body = render_markdown(section.body, id_prefix=f"{ident}-")
    return (
        f'<section class="rule-section" id="{ident}" data-section="{section.number}">'
        f'<header class="section-heading"><span class="section-number">{section.number:02d}</span>'
        f"<h2>{_inline(section.title)}</h2></header>{body}</section>"
    )


def heading_count(markdown: str) -> int:
    return sum(1 for line in markdown.splitlines() if HEADING_RE.match(line))


def find_section(sections: Iterable[Section], number: int) -> Section:
    return next(section for section in sections if section.number == number)
