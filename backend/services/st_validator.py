from __future__ import annotations

import logging
import re
from collections import Counter
from pathlib import Path
from typing import Any

from models.logic import CompletedLogicModel, RuntimeValidationResult, STGenerationResult, STValidationIssue, STValidationResult
from models.st_verifier import STVerifyResponse, STVerifierFileResult, STVerifierIssue, STVerifierSummary
from services.project_service import project_service
from services.st_parser_adapter import ParseIssue, STParserAdapter, build_parser
from services.st_codegen_utils import st_codegen_utils


def resolve_control_logic_root(workspace_path: str | Path) -> Path:
    """Resolve workspace input to the control logic root directory.

    Accepts either:
    - a direct `/control_logic` path, or
    - a parent path that contains a `control_logic` child directory.
    """

    raw = str(workspace_path).strip()
    candidate = Path(raw).expanduser()

    if candidate.exists():
        resolved_candidate = candidate.resolve()
        if resolved_candidate.name == "control_logic":
            return resolved_candidate
        nested = resolved_candidate / "control_logic"
        if nested.exists():
            return nested
        return resolved_candidate

    try:
        project_control_logic = project_service.workspace_paths(raw).control_logic
        return project_control_logic.resolve()
    except Exception:
        direct_project_control_logic = project_service.workspace_root / raw / "control_logic"
        if direct_project_control_logic.exists():
            return direct_project_control_logic.resolve()

    resolved_candidate = candidate.resolve()
    if resolved_candidate.name == "control_logic":
        return resolved_candidate
    nested = resolved_candidate / "control_logic"
    if nested.exists():
        return nested
    return resolved_candidate


def collect_st_files(workspace_path: str | Path) -> list[Path]:
    """Recursively collect all `.st` files from a workspace path."""

    root = resolve_control_logic_root(workspace_path)
    if not root.exists() or not root.is_dir():
        return []
    return sorted([path for path in root.rglob("*.st") if path.is_file()])


def parse_st_file(file_path: Path, parser: STParserAdapter | None = None) -> tuple[str, Any, list[ParseIssue]]:
    """Parse one ST file and return `(content, ast, parse_issues)`.

    Tree-Sitter hook:
    - If the adapter exposes `parse_to_ast`, this function will call it.
    - Otherwise it falls back to adapter `parse()` diagnostics while returning `ast=None`.
    """

    content = file_path.read_text(encoding="utf-8", errors="replace")
    st_parser = parser or build_parser()

    ast: Any = None
    parse_issues: list[ParseIssue] = []

    parse_to_ast = getattr(st_parser, "parse_to_ast", None)
    if callable(parse_to_ast):
        try:
            ast, parse_issues = parse_to_ast(content)
        except Exception as exc:
            parse_issues = [ParseIssue(line=1, message=f"Tree-Sitter parse_to_ast failure: {exc}")]
    else:
        try:
            parse_issues = st_parser.parse(content)
        except Exception as exc:
            parse_issues = [ParseIssue(line=1, message=f"Parser invocation failure: {exc}")]

    return content, ast, parse_issues


def detect_template_placeholders(content: str) -> list[STVerifierIssue]:
    """Detect unresolved template placeholders that must hard-fail verification."""

    issues: list[STVerifierIssue] = []
    patterns = [
        (r"\{\{[^}]+\}\}", "empty_template_section", "Unresolved template placeholder `{{...}}` found."),
        (r"\bTODO_GENERATE\b", "empty_template_section", "Unresolved `TODO_GENERATE` token found."),
        (r"__PLACEHOLDER__", "empty_template_section", "Unresolved `__PLACEHOLDER__` token found."),
    ]

    for line_no, line in enumerate(content.splitlines(), start=1):
        for pattern, code, message in patterns:
            if re.search(pattern, line):
                issues.append(STVerifierIssue(line=line_no, column=1, code=code, message=message))
    return issues


def _count(pattern: str, content: str) -> int:
    return len(re.findall(pattern, content, flags=re.IGNORECASE | re.MULTILINE))


def _routine_headers(content: str) -> list[tuple[int, str]]:
    headers: list[tuple[int, str]] = []
    header_re = re.compile(r"^\s*(PROGRAM|FUNCTION_BLOCK|FUNCTION)\b", flags=re.IGNORECASE)
    for line_no, line in enumerate(content.splitlines(), start=1):
        match = header_re.search(line)
        if match:
            headers.append((line_no, match.group(1).upper()))
    return headers


def _strip_comments(content: str) -> str:
    no_block_comments = re.sub(r"\(\*.*?\*\)", "", content, flags=re.DOTALL)
    no_line_comments = re.sub(r"//.*$", "", no_block_comments, flags=re.MULTILINE)
    return no_line_comments


def _is_empty_routine_body(content: str) -> bool:
    cleaned = _strip_comments(content)
    if not cleaned.strip():
        return True
    has_logic = re.search(
        r":=|\b(IF|CASE|FOR|WHILE|REPEAT|RETURN|EXIT|CONTINUE|ELSIF|ELSE)\b|\b[A-Z_][A-Z0-9_]*\s*\(",
        cleaned,
        flags=re.IGNORECASE,
    )
    return has_logic is None


def validate_ast(content: str, ast: Any, parse_issues: list[ParseIssue]) -> tuple[list[STVerifierIssue], list[STVerifierIssue]]:
    """Validate syntax and structural rules from parse diagnostics and textual fallbacks."""

    errors: list[STVerifierIssue] = []
    warnings: list[STVerifierIssue] = []

    if not content.strip():
        warnings.append(
            STVerifierIssue(
                line=1,
                column=1,
                code="routine_file_empty",
                message="Routine file exists but appears empty.",
            )
        )
        return errors, warnings

    for parse_issue in parse_issues:
        errors.append(
            STVerifierIssue(
                line=parse_issue.line or 1,
                column=1,
                code="parse_failure",
                message=parse_issue.message,
            )
        )

    if _count(r"^\s*IF\b", content) > _count(r"^\s*END_IF\s*;", content):
        errors.append(STVerifierIssue(line=1, column=1, code="missing_end_if", message="Missing END_IF for one or more IF blocks."))

    if _count(r"^\s*PROGRAM\b", content) > _count(r"^\s*END_PROGRAM\b", content):
        errors.append(
            STVerifierIssue(
                line=1,
                column=1,
                code="missing_end_program",
                message="Missing END_PROGRAM for one or more PROGRAM blocks.",
            )
        )

    case_count = _count(r"^\s*CASE\b", content)
    end_case_count = _count(r"^\s*END_CASE\s*;", content)
    if case_count != end_case_count:
        errors.append(
            STVerifierIssue(
                line=1,
                column=1,
                code="malformed_case",
                message="CASE/END_CASE block imbalance detected.",
            )
        )

    headers = _routine_headers(content)
    if not headers:
        errors.append(
            STVerifierIssue(
                line=1,
                column=1,
                code="undefined_routine_block_structure",
                message="No PROGRAM/FUNCTION_BLOCK/FUNCTION routine header detected.",
            )
        )

    fb_count = _count(r"^\s*FUNCTION_BLOCK\b", content)
    end_fb_count = _count(r"^\s*END_FUNCTION_BLOCK\b", content)
    if fb_count > end_fb_count:
        errors.append(
            STVerifierIssue(
                line=1,
                column=1,
                code="missing_end_function_block",
                message="Missing END_FUNCTION_BLOCK for one or more FUNCTION_BLOCK blocks.",
            )
        )

    fn_count = _count(r"^\s*FUNCTION\b", content)
    end_fn_count = _count(r"^\s*END_FUNCTION\b", content)
    if fn_count > end_fn_count:
        errors.append(
            STVerifierIssue(
                line=1,
                column=1,
                code="missing_end_function",
                message="Missing END_FUNCTION for one or more FUNCTION blocks.",
            )
        )

    errors.extend(detect_template_placeholders(content))

    for line_no, line in enumerate(content.splitlines(), start=1):
        upper = line.upper()
        if "TODO" in upper and "TODO_GENERATE" not in upper:
            warnings.append(
                STVerifierIssue(
                    line=line_no,
                    column=1,
                    code="todo_marker",
                    message="TODO marker left in generated ST code.",
                )
            )

    if headers and _is_empty_routine_body(content):
        warnings.append(
            STVerifierIssue(
                line=headers[0][0],
                column=1,
                code="empty_routine",
                message="Routine block is syntactically valid but has no executable logic.",
            )
        )

    return errors, warnings


def _display_file_path(control_logic_root: Path, file_path: Path) -> str:
    relative = file_path.relative_to(control_logic_root).as_posix()
    return f"{control_logic_root.name}/{relative}"


def aggregate_results(file_results: list[STVerifierFileResult]) -> dict:
    """Aggregate per-file verification diagnostics into project-level status."""

    error_count = sum(len(item.errors) for item in file_results)
    warning_count = sum(len(item.warnings) for item in file_results)

    if error_count > 0:
        status = "failed"
    elif warning_count > 0:
        status = "passed_with_warnings"
    else:
        status = "passed"

    response = STVerifyResponse(
        status=status,
        summary=STVerifierSummary(files_checked=len(file_results), error_count=error_count, warning_count=warning_count),
        files=file_results,
    )
    return response.model_dump()


def verify_st_workspace(workspace_path: str) -> dict:
    """Verify all generated ST files in a control logic workspace.

    This verifies the *entire* workspace recursively (not only `main.st`) and
    returns per-file diagnostics with blocking (`errors`) and non-blocking
    (`warnings`) classification.
    """

    control_logic_root = resolve_control_logic_root(workspace_path)
    st_files = collect_st_files(control_logic_root)
    parser = build_parser()

    if not st_files:
        empty_result = STVerifierFileResult(
            file=f"{control_logic_root.name}/",
            status="failed",
            errors=[
                STVerifierIssue(
                    line=1,
                    column=1,
                    code="workspace_empty",
                    message="No .st files found in workspace.",
                )
            ],
            warnings=[],
        )
        return aggregate_results([empty_result])

    file_results: list[STVerifierFileResult] = []
    for file_path in st_files:
        content, ast, parse_issues = parse_st_file(file_path, parser=parser)
        errors, warnings = validate_ast(content=content, ast=ast, parse_issues=parse_issues)

        if errors:
            file_status = "failed"
        elif warnings:
            file_status = "warnings"
        else:
            file_status = "passed"

        file_results.append(
            STVerifierFileResult(
                file=_display_file_path(control_logic_root, file_path),
                status=file_status,
                errors=errors,
                warnings=warnings,
            )
        )

    return aggregate_results(file_results)


class STValidator:
    """Strict production ST validation for structure, parser, and deployment readiness gates."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.parser = build_parser()

    @staticmethod
    def _count(pattern: str, text: str) -> int:
        return len(re.findall(pattern, text, flags=re.IGNORECASE | re.MULTILINE))

    @staticmethod
    def _iter_lines(content: str) -> list[tuple[int, str]]:
        return list(enumerate(content.splitlines(), start=1))

    @staticmethod
    def _is_comment_line(line: str) -> bool:
        stripped = line.strip()
        return stripped.startswith("(*") or stripped.startswith("//")

    @staticmethod
    def _extract_declared_symbols(content: str) -> list[tuple[str, int]]:
        declared: list[tuple[str, int]] = []
        in_var = False
        for line_no, line in enumerate(content.splitlines(), start=1):
            upper = line.strip().upper()
            if upper in {"VAR", "VAR_INPUT", "VAR_OUTPUT", "VAR_IN_OUT", "VAR_EXTERNAL", "VAR_TEMP"}:
                in_var = True
                continue
            if in_var and upper == "END_VAR":
                in_var = False
                continue
            if not in_var:
                continue
            match = re.match(r"\s*([A-Z_][A-Z0-9_]*)\s*:\s*[A-Z_][A-Z0-9_]*(?:\s*:=.+)?;\s*$", line, flags=re.IGNORECASE)
            if match:
                declared.append((match.group(1).upper(), line_no))
        return declared

    @staticmethod
    def _extract_assignments(content: str) -> list[tuple[int, str]]:
        output: list[tuple[int, str]] = []
        for line_no, line in enumerate(content.splitlines(), start=1):
            match = re.match(r"\s*([A-Z_][A-Z0-9_]*)\s*:=\s*.+;\s*$", line, flags=re.IGNORECASE)
            if match:
                output.append((line_no, match.group(1).upper()))
        return output

    @staticmethod
    def _has_duplicate_var_sections(content: str) -> list[str]:
        sections = re.findall(r"^\s*(VAR(?:_INPUT|_OUTPUT|_IN_OUT|_EXTERNAL|_TEMP|_GLOBAL)?)\s*$", content, flags=re.IGNORECASE | re.MULTILINE)
        section_count = Counter(token.upper() for token in sections)
        return [name for name, count in section_count.items() if count > 1]

    def _validate_file_structure(self, relative_path: str, content: str) -> list[STValidationIssue]:
        issues: list[STValidationIssue] = []
        upper = content.upper()

        if not content.strip():
            issues.append(
                STValidationIssue(
                    file=relative_path,
                    rule="empty_file",
                    message="Generated ST file is empty.",
                    severity="error",
                    line=1,
                )
            )
            return issues

        # Tree-sitter parser backend required.
        if self.parser.name != "tree-sitter-st":
            issues.append(
                STValidationIssue(
                    file=relative_path,
                    rule="parser_backend_not_treesitter",
                    message="Production validation requires Tree-Sitter ST parser backend.",
                    severity="error",
                    line=1,
                    source=self.parser.name,
                )
            )

        for parse_issue in self.parser.parse(content):
            issues.append(
                STValidationIssue(
                    file=relative_path,
                    rule="tree_sitter_parse_error",
                    message=parse_issue.message,
                    severity="error",
                    line=parse_issue.line,
                    source=self.parser.name,
                )
            )

        # Hard balance checks.
        if self._count(r"^\s*IF\b", content) != self._count(r"^\s*END_IF\s*;", content):
            issues.append(
                STValidationIssue(
                    file=relative_path,
                    rule="if_end_if_balance",
                    message="IF/END_IF block mismatch.",
                    severity="error",
                )
            )

        if self._count(r"^\s*CASE\b", content) != self._count(r"^\s*END_CASE\s*;", content):
            issues.append(
                STValidationIssue(
                    file=relative_path,
                    rule="case_end_case_balance",
                    message="CASE/END_CASE block mismatch.",
                    severity="error",
                )
            )

        if self._count(r"^\s*VAR(?:_INPUT|_OUTPUT|_IN_OUT|_EXTERNAL|_TEMP|_GLOBAL)?\s*$", content) != self._count(r"^\s*END_VAR\s*$", content):
            issues.append(
                STValidationIssue(
                    file=relative_path,
                    rule="var_end_var_balance",
                    message="VAR/END_VAR block mismatch.",
                    severity="error",
                )
            )

        duplicate_sections = self._has_duplicate_var_sections(content)
        for section in duplicate_sections:
            issues.append(
                STValidationIssue(
                    file=relative_path,
                    rule="duplicate_var_section",
                    message=f"Duplicate {section} section in the same routine file.",
                    severity="error",
                )
            )

        # Routine closure checks.
        program_count = self._count(r"^\s*PROGRAM\b", content)
        end_program_count = self._count(r"^\s*END_PROGRAM\b", content)
        fb_count = self._count(r"^\s*FUNCTION_BLOCK\b", content)
        end_fb_count = self._count(r"^\s*END_FUNCTION_BLOCK\b", content)
        fn_count = self._count(r"^\s*FUNCTION\b", content)
        end_fn_count = self._count(r"^\s*END_FUNCTION\b", content)

        if relative_path == "main.st":
            if program_count != 1 or end_program_count != 1:
                issues.append(
                    STValidationIssue(
                        file=relative_path,
                        rule="main_program_structure",
                        message="main.st must contain exactly one PROGRAM/END_PROGRAM pair.",
                        severity="error",
                    )
                )
        else:
            if program_count > 0:
                issues.append(
                    STValidationIssue(
                        file=relative_path,
                        rule="non_main_contains_program",
                        message="Non-main ST files must not declare PROGRAM blocks.",
                        severity="error",
                    )
                )

        if fb_count != end_fb_count:
            issues.append(
                STValidationIssue(
                    file=relative_path,
                    rule="function_block_closure",
                    message="FUNCTION_BLOCK/END_FUNCTION_BLOCK mismatch.",
                    severity="error",
                )
            )

        if fn_count != end_fn_count:
            issues.append(
                STValidationIssue(
                    file=relative_path,
                    rule="function_closure",
                    message="FUNCTION/END_FUNCTION mismatch.",
                    severity="error",
                )
            )

        # Duplicate declarations in the same file.
        declared = self._extract_declared_symbols(content)
        declared_counts = Counter(name for name, _ in declared)
        for symbol, count in sorted(declared_counts.items()):
            if count > 1:
                first_line = next((line for name, line in declared if name == symbol), None)
                issues.append(
                    STValidationIssue(
                        file=relative_path,
                        rule="duplicate_declaration",
                        message=f"Duplicate declaration for symbol {symbol} in same file.",
                        severity="error",
                        line=first_line,
                        involved_tags=[symbol],
                    )
                )

        # Client-ready cleanliness: do not expose evidence metadata comments.
        for line_no, line in self._iter_lines(content):
            if re.search(r"(CONFIRMED FROM DOCUMENT|DOCUMENT CONFLICT|ENGINEERING DEFAULT|PARTIALLY CONFIRMED)", line, flags=re.IGNORECASE):
                issues.append(
                    STValidationIssue(
                        file=relative_path,
                        rule="evidence_comment_exposed",
                        message="Client ST file exposes internal evidence metadata comments.",
                        severity="error",
                        line=line_no,
                    )
                )

        # Reject TODO placeholders and malformed explicit placeholders.
        if "TODO" in upper:
            issues.append(
                STValidationIssue(
                    file=relative_path,
                    rule="todo_placeholder",
                    message="Generated ST contains TODO placeholders.",
                    severity="error",
                )
            )

        if re.search(r"^\s*IF\s+FALSE\s+THEN\s*$", content, flags=re.IGNORECASE | re.MULTILINE):
            issues.append(
                STValidationIssue(
                    file=relative_path,
                    rule="literal_false_scaffold",
                    message="Generated ST contains literal IF FALSE scaffold branch.",
                    severity="error",
                )
            )

        return issues

    @staticmethod
    def _expected_path_set(model: CompletedLogicModel) -> set[str]:
        def stem(raw: str) -> str:
            symbol = re.sub(r"[^a-z0-9_]+", "_", st_codegen_utils.normalize_symbol(raw).lower())
            symbol = re.sub(r"_+", "_", symbol).strip("_")
            return symbol or "routine"

        expected = {"main.st", "utilities/utilities.st"}
        expected.update({f"equipment/{stem(item.equipment_tag)}.st" for item in model.equipment_routines})
        expected.update({f"control_loops/{stem(item.loop_tag)}.st" for item in model.loops})
        expected.update({f"interlocks/{stem(item.interlock_id)}.st" for item in model.interlocks})
        expected.update({f"alarms/{stem(item.group_name)}.st" for item in model.alarm_groups})
        if model.startup_sequence:
            expected.add("sequences/startup_sequence.st")
        if model.shutdown_sequence:
            expected.add("sequences/shutdown_sequence.st")
        return expected

    def validate(
        self,
        project_id: str,
        generation_result: STGenerationResult,
        model: CompletedLogicModel | None = None,
        runtime_validation: RuntimeValidationResult | None = None,
    ) -> STValidationResult:
        issues: list[STValidationIssue] = []

        file_paths = [item.relative_path for item in generation_result.files]
        path_counts = Counter(file_paths)
        for rel, count in sorted(path_counts.items()):
            if count > 1:
                issues.append(
                    STValidationIssue(
                        file=rel,
                        rule="duplicate_output_file",
                        message=f"Generated duplicate output file path {rel} ({count} copies).",
                        severity="error",
                    )
                )

        assignment_writers: dict[str, list[tuple[str, int]]] = {}
        for item in generation_result.files:
            content_issues = self._validate_file_structure(item.relative_path, item.content)
            issues.extend(content_issues)
            for line_no, lhs in self._extract_assignments(item.content):
                assignment_writers.setdefault(lhs, []).append((item.relative_path, line_no))

        # Cross-file duplicate writer conflicts for analog outputs.
        for symbol, refs in sorted(assignment_writers.items()):
            if not symbol.endswith("_OUT"):
                continue
            files = {file_name for file_name, _ in refs}
            if len(files) > 1:
                issues.append(
                    STValidationIssue(
                        file=sorted(files)[0],
                        rule="multi_block_output_writer_conflict",
                        message=f"Output {symbol} is written in multiple routine files.",
                        severity="error",
                        line=refs[0][1],
                        involved_tags=[symbol],
                    )
                )

        # Required model objects must exist for production output.
        if model is not None:
            if not model.equipment_routines:
                issues.append(
                    STValidationIssue(
                        file="main.st",
                        rule="missing_required_equipment_routines",
                        message="No equipment routines were generated in completed logic model.",
                        severity="error",
                    )
                )
            if not model.loops:
                issues.append(
                    STValidationIssue(
                        file="main.st",
                        rule="missing_required_control_loops",
                        message="No control loops were generated in completed logic model.",
                        severity="error",
                    )
                )
            if not model.interlocks:
                issues.append(
                    STValidationIssue(
                        file="main.st",
                        rule="missing_required_interlocks",
                        message="No interlocks were generated in completed logic model.",
                        severity="error",
                    )
                )
            if not model.alarm_groups:
                issues.append(
                    STValidationIssue(
                        file="main.st",
                        rule="missing_required_alarms",
                        message="No alarm groups were generated in completed logic model.",
                        severity="error",
                    )
                )
            if not model.startup_sequence:
                issues.append(
                    STValidationIssue(
                        file="sequences/startup_sequence.st",
                        rule="missing_required_startup_sequence",
                        message="Startup sequence is required for production output.",
                        severity="error",
                    )
                )
            if not model.shutdown_sequence:
                issues.append(
                    STValidationIssue(
                        file="sequences/shutdown_sequence.st",
                        rule="missing_required_shutdown_sequence",
                        message="Shutdown sequence is required for production output.",
                        severity="error",
                    )
                )

            expected = self._expected_path_set(model)
            actual = set(file_paths)
            missing_files = sorted(expected - actual)
            for rel in missing_files:
                issues.append(
                    STValidationIssue(
                        file=rel,
                        rule="missing_required_output_file",
                        message=f"Required routine file {rel} was not generated.",
                        severity="error",
                    )
                )

        # Runtime readiness hook must pass for production acceptance.
        if runtime_validation is not None and runtime_validation.status != "ready":
            issues.append(
                STValidationIssue(
                    file="main.st",
                    rule="runtime_load_failed",
                    message="OpenPLC runtime readiness hook reported failure.",
                    severity="error",
                    source="runtime_deployer.validate_openplc_readiness",
                )
            )

        valid = not any(issue.severity == "error" for issue in issues)
        self.logger.info("ST validation completed: project=%s valid=%s issues=%s", project_id, valid, len(issues))
        return STValidationResult(project_id=project_id, valid=valid, issues=issues, parser_backend=self.parser.name)


st_validator = STValidator()
