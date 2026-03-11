from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ParseIssue:
    line: int
    message: str


class STParserAdapter:
    name: str = "fallback-regex"

    def parse(self, content: str) -> list[ParseIssue]:
        raise NotImplementedError


class FallbackRegexSTParser(STParserAdapter):
    name = "fallback-regex"

    def parse(self, content: str) -> list[ParseIssue]:
        issues: list[ParseIssue] = []
        lines = content.splitlines()
        if not any("PROGRAM" in line.upper() or "FUNCTION_BLOCK" in line.upper() for line in lines):
            issues.append(ParseIssue(line=1, message="Missing PROGRAM/FUNCTION_BLOCK header"))
        return issues


class TreeSitterSTParser(STParserAdapter):
    name = "tree-sitter-st"

    def __init__(self) -> None:
        # TODO: wire real tree-sitter grammar loading when grammar dependency is available.
        pass

    def parse(self, content: str) -> list[ParseIssue]:
        # TODO: replace with actual tree-sitter parse diagnostics.
        return []


def build_parser() -> STParserAdapter:
    try:
        return TreeSitterSTParser()
    except Exception:
        return FallbackRegexSTParser()
