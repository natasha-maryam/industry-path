from __future__ import annotations

import logging
import re
from collections import Counter

from models.logic import CompletedLogicModel, RuntimeValidationResult, STGenerationResult, STValidationIssue, STValidationResult
from services.st_parser_adapter import build_parser
from services.st_codegen_utils import st_codegen_utils


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
