from __future__ import annotations

import json
import logging
import os
import re
import shutil
import signal
import subprocess
from pathlib import Path
from typing import Any

from services.st_codegen_utils import st_codegen_utils


class BeremizAdapter:
    """Headless runtime adapter (matiec + gcc/make) with Beremiz-compatible naming."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.projects_root = Path(os.getenv("BEREMIZ_RUNTIME_PROJECTS_ROOT", "runtime_projects")).resolve()
        self.projects_root.mkdir(parents=True, exist_ok=True)
        self.runtime_binary_name = os.getenv("BEREMIZ_RUNTIME_BINARY", "runtime_binary")
        self._active_project_dir: Path | None = None
        self._runtime_process: subprocess.Popen[str] | None = None

    @staticmethod
    def _which(command: str) -> str | None:
        return shutil.which(command)

    @staticmethod
    def _detect_version(command: str) -> str | None:
        executable = shutil.which(command)
        if not executable:
            return None
        candidates = [
            [executable, "--version"],
            [executable, "-v"],
            [executable, "-V"],
        ]
        for probe in candidates:
            try:
                completed = subprocess.run(
                    probe,
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
            except Exception:
                continue
            output = (completed.stdout or "") + "\n" + (completed.stderr or "")
            first_line = next((line.strip() for line in output.splitlines() if line.strip()), "")
            if first_line:
                return first_line
        return None

    @staticmethod
    def _resolve_executable(command: str) -> str | None:
        path_candidate = shutil.which(command)
        if path_candidate:
            return path_candidate

        env_key = f"{command.upper()}_PATH"
        env_path = os.getenv(env_key)
        if env_path and Path(env_path).exists() and os.access(env_path, os.X_OK):
            return env_path

        if command == "iec2c":
            explicit_candidates = [
                os.getenv("MATIEC_IEC2C_PATH", "").strip(),
                os.getenv("IEC2C_PATH", "").strip(),
                "/Users/apple/Beremiz/matiec/iec2c",
                str(Path.home() / "Beremiz" / "matiec" / "iec2c"),
                str(Path.home() / ".local" / "bin" / "iec2c"),
            ]
            for candidate in explicit_candidates:
                if not candidate:
                    continue
                candidate_path = Path(candidate).expanduser()
                if candidate_path.exists() and os.access(candidate_path, os.X_OK):
                    return str(candidate_path)

        return None

    @staticmethod
    def _resolve_matiec_lib_dir(iec2c_path: str | None) -> str | None:
        env_candidates = [
            os.getenv("MATIEC_LIB_DIR", "").strip(),
            os.getenv("IEC2C_LIB_DIR", "").strip(),
        ]
        for candidate in env_candidates:
            if not candidate:
                continue
            candidate_path = Path(candidate).expanduser()
            if (candidate_path / "ieclib.txt").exists():
                return str(candidate_path)

        if iec2c_path:
            parent = Path(iec2c_path).resolve().parent
            sibling_lib = parent / "lib"
            if (sibling_lib / "ieclib.txt").exists():
                return str(sibling_lib)

        default_candidates = [
            Path.home() / "Beremiz" / "matiec" / "lib",
            Path("/Users/apple/Beremiz/matiec/lib"),
            Path.home() / ".local" / "share" / "matiec" / "lib",
        ]
        for candidate in default_candidates:
            if (candidate / "ieclib.txt").exists():
                return str(candidate)

        return None

    @staticmethod
    def _sanitize_empty_var_blocks(content: str) -> str:
        pattern = re.compile(r"VAR\n(.*?)\nEND_VAR", re.S)

        def _replace(match: re.Match[str]) -> str:
            body = match.group(1)
            if ":" in body:
                return match.group(0)
            return "VAR\n    CLX_DUMMY : BOOL := FALSE;\nEND_VAR"

        return pattern.sub(_replace, content)

    @staticmethod
    def _rewrite_var_global_for_state_manager(content: str) -> str:
        if "FUNCTION_BLOCK FB_SYSTEM_STATE_MANAGER" not in content or "VAR_GLOBAL" not in content:
            return content

        match = re.search(r"\bVAR_GLOBAL\b\s*(.*?)\bEND_VAR\b", content, flags=re.S | re.I)
        if not match:
            return content

        declarations: list[str] = []
        for line in match.group(1).splitlines():
            stripped = line.strip()
            if ":" not in stripped or not stripped.endswith(";"):
                continue
            normalized = re.sub(r"\s*:=\s*[^;]+;", ";", line)
            declarations.append(normalized.rstrip())

        content = content[: match.start()] + content[match.end() :]
        if not declarations:
            return content

        external_block = "VAR_EXTERNAL\n" + "\n".join(declarations) + "\nEND_VAR\n\n"
        return re.sub(
            r"(\bFUNCTION_BLOCK\s+FB_SYSTEM_STATE_MANAGER\b\s*)",
            r"\1\n" + external_block,
            content,
            count=1,
        )

    @staticmethod
    def _normalize_bool_subtractions(content: str) -> str:
        bool_vars = set(re.findall(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*BOOL\b", content, flags=re.M))
        if not bool_vars:
            return content

        def _cast_if_bool(token: str) -> str:
            return f"BOOL_TO_REAL({token})" if token in bool_vars else token

        def _replace(match: re.Match[str]) -> str:
            lhs = match.group(1)
            left = match.group(2)
            right = match.group(3)
            return f"{lhs}{_cast_if_bool(left)} - {_cast_if_bool(right)};"

        return re.sub(
            r"(^\s*[A-Za-z_][A-Za-z0-9_]*\s*:=\s*)([A-Za-z_][A-Za-z0-9_]*)\s*-\s*([A-Za-z_][A-Za-z0-9_]*)\s*;",
            _replace,
            content,
            flags=re.M,
        )

    @staticmethod
    def _inject_main_instance_declarations(content: str, known_function_blocks: set[str]) -> str:
        calls = sorted(set(re.findall(r"^\s*(INST_[A-Z0-9_]+)\s*\(\s*\)\s*;\s*$", content, flags=re.M)))
        if not calls:
            return content

        declarations: list[str] = []
        for instance in calls:
            fb_name = f"FB_{instance[5:]}"
            if known_function_blocks and fb_name not in known_function_blocks:
                continue
            declarations.append(f"    {instance} : {fb_name};")

        if not declarations:
            return content

        var_match = re.search(r"\bVAR\b", content)
        if not var_match:
            return content

        insert_pos = var_match.end()
        injected = "\n" + "\n".join(declarations)
        return content[:insert_pos] + injected + content[insert_pos:]

    @staticmethod
    def _shorten_long_identifiers(content: str, max_len: int = 20) -> str:
        token_re = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
        mapping: dict[str, str] = {}
        counter = 0

        keywords = {
            "PROGRAM",
            "END_PROGRAM",
            "FUNCTION_BLOCK",
            "END_FUNCTION_BLOCK",
            "FUNCTION",
            "END_FUNCTION",
            "VAR",
            "VAR_INPUT",
            "VAR_OUTPUT",
            "VAR_IN_OUT",
            "VAR_EXTERNAL",
            "VAR_TEMP",
            "END_VAR",
            "IF",
            "THEN",
            "ELSE",
            "ELSIF",
            "END_IF",
            "FOR",
            "DO",
            "END_FOR",
            "WHILE",
            "END_WHILE",
            "REPEAT",
            "UNTIL",
            "END_REPEAT",
            "CASE",
            "OF",
            "END_CASE",
            "BOOL",
            "REAL",
            "INT",
            "DINT",
            "LREAL",
            "STRING",
            "TRUE",
            "FALSE",
        }

        force_rename_tokens = {
            "FIRST",
            "SECOND",
            "THIRD",
            "FOURTH",
            "LAST",
            "MAIN",
            "ERROR",
            "INTEGRAL",
            "PREV_ERROR",
            "P_TERM",
            "I_TERM",
            "D_TERM",
        }

        def _replace(match: re.Match[str]) -> str:
            nonlocal counter
            token = match.group(0)
            token_upper = token.upper()
            if token_upper in keywords:
                return token
            if len(token) <= max_len and token_upper not in force_rename_tokens:
                return token
            if token not in mapping:
                counter += 1
                mapping[token] = f"CLX_{counter:04d}"
            return mapping[token]

        return token_re.sub(_replace, content)

    def _build_bundle_source(self, project_dir: Path, st_files: list[Path]) -> tuple[Path, str]:
        bundle_path = project_dir / "build" / "bundle_main.st"
        ordered = sorted(st_files, key=lambda item: (item.name.lower() == "main.st", item.name.lower()))

        main_file = project_dir / "main.st"
        if main_file.exists():
            main_content = main_file.read_text()
            if "(* ===== FILE:" in main_content:
                ordered = [main_file]

        preamble = """
TYPE
    PLANT_STATE : (PLANT_STOPPED, PLANT_STARTING, PLANT_RUNNING, PLANT_STOPPING, PLANT_FAULT);
END_TYPE
""".strip()

        parts: list[str] = []
        known_function_blocks: set[str] = set()
        for source in ordered:
            text = source.read_text()
            known_function_blocks.update(re.findall(r"\bFUNCTION_BLOCK\s+([A-Za-z_][A-Za-z0-9_]*)", text))

        for source in ordered:
            text = source.read_text()
            text = re.sub(r"^\s*\(\*\s*=+\s*FILE:.*?\*\)\s*$", "", text, flags=re.M)
            text = self._sanitize_empty_var_blocks(text)
            text = re.sub(r"\bTYPE\s+PLANT_STATE\s*:\s*\([^;]*\)\s*;\s*END_TYPE\s*", "", text, flags=re.I | re.S)
            text = self._rewrite_var_global_for_state_manager(text)

            if re.fullmatch(r"\s*VAR_GLOBAL\b[\s\S]*\bEND_VAR\b\s*", text, flags=re.I):
                continue

            if source.name.lower() == "main.st":
                text = self._inject_main_instance_declarations(text, known_function_blocks)
            parts.append(text.strip())

        bundle_sections: list[str] = [preamble]
        bundle_sections.extend([part for part in parts if part])

        bundle_content = "\n\n".join(bundle_sections) + "\n"
        bundle_content = self._shorten_long_identifiers(bundle_content)
        bundle_content = self._normalize_bool_subtractions(bundle_content)
        bundle_path.write_text(bundle_content)
        return bundle_path, bundle_content

    @staticmethod
    def _ensure_global_accessor_bindings(generated_c_dir: Path) -> None:
        pous_header = generated_c_dir / "POUS.h"
        if not pous_header.exists():
            return

        pous_text = pous_header.read_text()
        required_scalars = {
            name: type_name
            for type_name, name in re.findall(r"__DECLARE_EXTERNAL\((\w+),(\w+)\)", pous_text)
        }
        required_fbs = {
            name: type_name
            for type_name, name in re.findall(r"__DECLARE_EXTERNAL_FB\((\w+),(\w+)\)", pous_text)
        }
        if not required_scalars and not required_fbs:
            return

        located_header = generated_c_dir / "LOCATED_VARIABLES.h"
        located_text = located_header.read_text() if located_header.exists() else ""

        declared_scalars = {
            name for _, _, name in re.findall(r"__DECLARE_GLOBAL\((\w+),(\w+),(\w+)\)", located_text)
        }
        declared_fbs = {
            name for _, _, name in re.findall(r"__DECLARE_GLOBAL_FB\((\w+),(\w+),(\w+)\)", located_text)
        }

        scalar_lines = [
            f"__DECLARE_GLOBAL({required_scalars[name]},RUNTIME_GLOBAL,{name})"
            for name in sorted(required_scalars.keys())
            if name not in declared_scalars
        ]
        fb_lines = [
            f"__DECLARE_GLOBAL_FB({required_fbs[name]},RUNTIME_GLOBAL,{name})"
            for name in sorted(required_fbs.keys())
            if name not in declared_fbs
        ]
        synthesized_lines = scalar_lines + fb_lines
        if not synthesized_lines:
            return

        if not located_text.strip():
            new_content = "\n".join(
                [
                    "#ifndef __LOCATED_VARIABLES_H",
                    "#define __LOCATED_VARIABLES_H",
                    "",
                    "#include \"accessor.h\"",
                    "",
                    *synthesized_lines,
                    "",
                    "#endif",
                    "",
                ]
            )
            located_header.write_text(new_content)
            return

        existing = located_text.rstrip()
        if "#endif" in existing:
            idx = existing.rfind("#endif")
            updated = existing[:idx].rstrip() + "\n\n" + "\n".join(synthesized_lines) + "\n\n" + existing[idx:] + "\n"
        else:
            updated = existing + "\n\n" + "\n".join(synthesized_lines) + "\n"
        located_header.write_text(updated)

    @staticmethod
    def _extract_declared_global_names(st_sources: list[Path]) -> set[str]:
        declared: set[str] = set()
        block_pattern = re.compile(r"\b(VAR|VAR_INPUT|VAR_OUTPUT|VAR_EXTERNAL|VAR_IN_OUT|VAR_TEMP|VAR_GLOBAL)\b(.*?)\bEND_VAR\b", flags=re.S | re.I)
        declaration_pattern = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:", flags=re.M)
        for source in st_sources:
            text = source.read_text()
            for _, block in block_pattern.findall(text):
                for match in declaration_pattern.finditer(block):
                    declared.add(match.group(1))
        return declared

    @staticmethod
    def _engineering_error(
        *,
        code: str,
        message: str,
        variable: str,
        source_file: str,
        stage: str,
        suggestion: str,
    ) -> dict[str, Any]:
        return {
            "success": False,
            "error_code": code,
            "message": message,
            "details": {
                "variable": variable,
                "source_file": source_file,
                "stage": stage,
                "suggestion": suggestion,
            },
        }

    def _validate_generated_externals(
        self,
        project_dir: Path,
        *,
        st_sources: list[Path],
        allowed_registry: set[str],
        runtime_catalog: set[str],
    ) -> list[dict[str, Any]]:
        generated_c_dir = project_dir / "generated_c"
        pous_header = generated_c_dir / "POUS.h"
        located_header = generated_c_dir / "LOCATED_VARIABLES.h"
        if not pous_header.exists():
            return [
                self._engineering_error(
                    code="MISSING_GENERATED_HEADER",
                    message="POUS.h was not generated by ST compile output.",
                    variable="POUS.h",
                    source_file="generated_c/POUS.h",
                    stage="compile_st",
                    suggestion="Verify ST generation and iec2c output before runtime packaging.",
                )
            ]

        declared_globals = self._extract_declared_global_names(st_sources)
        allowed_all = {item for item in allowed_registry if item}
        allowed_all.update(declared_globals)

        content = pous_header.read_text()
        required_externals = {
            name for _, name in re.findall(r"__DECLARE_EXTERNAL\((\w+),(\w+)\)", content)
        }
        required_externals.update(
            name for _, name in re.findall(r"__DECLARE_EXTERNAL_FB\((\w+),(\w+)\)", content)
        )

        located_text = located_header.read_text() if located_header.exists() else ""
        declared_located = {
            name for _, _, name in re.findall(r"__DECLARE_GLOBAL\((\w+),(\w+),(\w+)\)", located_text)
        }
        declared_located.update(
            name for _, _, name in re.findall(r"__DECLARE_GLOBAL_FB\((\w+),(\w+),(\w+)\)", located_text)
        )

        errors: list[dict[str, Any]] = []
        for variable in sorted(required_externals):
            if re.fullmatch(r"CLX_\d+", variable):
                continue
            if variable in declared_located:
                continue
            if variable in allowed_all:
                continue

            source_guess = next((item.name for item in st_sources if variable in item.read_text()), st_sources[0].name if st_sources else "unknown")
            errors.append(
                self._engineering_error(
                    code="UNDECLARED_ST_VARIABLE",
                    message=f"Structured Text references variable `{variable}` but it is not declared in the generated logic model or IO mapping.",
                    variable=variable,
                    source_file=source_guess,
                    stage="compile_st",
                    suggestion="Declare the variable in the logic model or generate the required IO/tag binding before deployment.",
                )
            )

        available_for_dependency = allowed_all | required_externals | declared_located | runtime_catalog
        for variable in sorted(required_externals):
            dependencies = st_codegen_utils.infer_command_dependencies(variable)
            if not dependencies:
                continue
            expected_tags = [
                *dependencies.get("status_tags", []),
                *dependencies.get("fault_tags", []),
            ]
            for expected in expected_tags:
                if expected in available_for_dependency:
                    continue
                source_guess = next((item.name for item in st_sources if variable in item.read_text()), st_sources[0].name if st_sources else "unknown")
                errors.append(
                    self._engineering_error(
                        code="MISSING_DEPENDENT_SIGNAL",
                        message=f"Structured Text command tag `{variable}` requires dependent signal `{expected}` but no declaration or tag binding was found.",
                        variable=expected,
                        source_file=source_guess,
                        stage="compile_st",
                        suggestion="Add the missing status/fault signal in the logic model or IO/tag registry before deployment.",
                    )
                )

        return errors

    @staticmethod
    def _write_runtime_main_stub(project_dir: Path) -> None:
        runtime_main = project_dir / "runtime_main.c"
        runtime_main.write_text(
            "\n".join(
                [
                    "#include \"POUS.h\"",
                    "",
                    "int main(void) {",
                    "    return 0;",
                    "}",
                    "",
                ]
            )
        )

    def dependency_report(self) -> dict[str, Any]:
        iec2c_path = self._resolve_executable("iec2c")
        dependencies = {
            "iec2c": iec2c_path,
            "beremiz": self._which("beremiz"),
            "gcc": self._which("gcc"),
            "make": self._which("make"),
            "python3": self._which("python3"),
            "matiec_lib": self._resolve_matiec_lib_dir(iec2c_path),
        }
        versions = {
            "iec2c": self._detect_version("iec2c"),
            "beremiz": self._detect_version("beremiz"),
            "gcc": self._detect_version("gcc"),
            "make": self._detect_version("make"),
            "python3": self._detect_version("python3"),
        }
        missing = [name for name in ("iec2c", "matiec_lib", "gcc", "make", "python3") if not dependencies.get(name)]
        return {
            "ok": len(missing) == 0,
            "dependencies": dependencies,
            "versions": versions,
            "missing": missing,
        }

    def _run_cmd(self, command: list[str], cwd: Path | None = None, timeout_seconds: int = 120) -> tuple[bool, str]:
        try:
            completed = subprocess.run(
                command,
                cwd=str(cwd) if cwd else None,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except Exception as exc:
            return False, f"Command execution error for {' '.join(command)}: {exc}"

        output = "\n".join([completed.stdout.strip(), completed.stderr.strip()]).strip()
        self.logger.info("runtime_engine cmd=%s rc=%s cwd=%s", " ".join(command), completed.returncode, cwd)
        if completed.returncode != 0:
            return False, f"Command failed ({completed.returncode}) {' '.join(command)} :: {output}"
        return True, output or "ok"

    @staticmethod
    def _step(name: str, status: str, message: str, detail: dict[str, Any] | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"name": name, "status": status, "message": message}
        if detail:
            payload["detail"] = detail
        return payload

    def create_runtime_project(self, project_id: str, st_files: list[Path]) -> tuple[bool, str, Path]:
        project_dir = self.projects_root / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "build").mkdir(parents=True, exist_ok=True)
        generated_c_dir = project_dir / "generated_c"
        generated_c_dir.mkdir(parents=True, exist_ok=True)

        if not st_files:
            return False, "No ST files provided for runtime project creation.", project_dir

        copied: list[str] = []
        for st_file in st_files:
            target = project_dir / st_file.name
            target.write_text(st_file.read_text())
            copied.append(st_file.name)

        if not (project_dir / "main.st").exists():
            first = project_dir / st_files[0].name
            (project_dir / "main.st").write_text(first.read_text())
            copied.append("main.st")

        self._write_makefile(project_dir)
        self._active_project_dir = project_dir
        return True, f"Runtime project prepared at {project_dir} with {len(copied)} ST artifact(s).", project_dir

    def _write_makefile(self, project_dir: Path) -> None:
        makefile = project_dir / "Makefile"
        lines = [
            "CC ?= gcc",
            "CFLAGS ?= -O2 -Wall -w",
            "MATIEC_LIB_DIR ?= /Users/apple/Beremiz/matiec/lib",
            "MATIEC_C_DIR := $(MATIEC_LIB_DIR)/C",
            "GENERATED_DIR := generated_c",
            "BUILD_DIR := build",
            "SOURCES := $(wildcard $(GENERATED_DIR)/*.c)",
            "RUNTIME_MAIN := runtime_main.c",
            "SOURCES += $(RUNTIME_MAIN)",
            "OBJECTS := $(patsubst $(GENERATED_DIR)/%.c,$(BUILD_DIR)/%.o,$(SOURCES))",
            "OBJECTS := $(patsubst %.c,$(BUILD_DIR)/%.o,$(OBJECTS))",
            f"TARGET := {self.runtime_binary_name}",
            "",
            "all: $(TARGET)",
            "",
            "$(TARGET): $(OBJECTS)",
            "\t$(CC) $(CFLAGS) -o $@ $(OBJECTS)",
            "",
            "$(BUILD_DIR)/%.o: $(GENERATED_DIR)/%.c",
            "\t@mkdir -p $(BUILD_DIR)",
            "\t$(CC) $(CFLAGS) -I $(GENERATED_DIR) -I $(MATIEC_C_DIR) -include $(GENERATED_DIR)/POUS.h -include $(GENERATED_DIR)/LOCATED_VARIABLES.h -c $< -o $@",
            "",
            "$(BUILD_DIR)/runtime_main.o: runtime_main.c",
            "\t@mkdir -p $(BUILD_DIR)",
            "\t$(CC) $(CFLAGS) -I $(GENERATED_DIR) -I $(MATIEC_C_DIR) -include $(GENERATED_DIR)/POUS.h -c $< -o $@",
            "",
            "clean:",
            "\trm -rf $(BUILD_DIR) $(TARGET)",
            "",
        ]
        content = "\n".join(lines)
        makefile.write_text(content)
        self._write_runtime_main_stub(project_dir)

    def compile_st(
        self,
        project_dir: Path,
        *,
        allowed_registry: set[str] | None = None,
        runtime_catalog: set[str] | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        st_files = sorted(project_dir.glob("*.st"))
        if not st_files:
            return False, self._step("compile_st", "failed", f"No .st files found in {project_dir}.")

        iec2c_cmd = self._resolve_executable("iec2c")
        if not iec2c_cmd:
            return False, self._step("compile_st", "failed", "iec2c compiler is not available in PATH or configured executable paths.")

        matiec_lib_dir = self._resolve_matiec_lib_dir(iec2c_cmd)
        if not matiec_lib_dir:
            return False, self._step("compile_st", "failed", "matiec library directory (ieclib.txt) not found.")

        generated_c_dir = project_dir / "generated_c"
        generated_c_dir.mkdir(parents=True, exist_ok=True)
        for artifact in generated_c_dir.glob("*.c"):
            artifact.unlink(missing_ok=True)
        for artifact in generated_c_dir.glob("*.h"):
            artifact.unlink(missing_ok=True)

        bundle_path, _ = self._build_bundle_source(project_dir, st_files)

        compile_cmd = [
            iec2c_cmd,
            "-p",
            "-I",
            matiec_lib_dir,
            "-T",
            str(generated_c_dir),
            str(bundle_path),
        ]
        ok, output = self._run_cmd(compile_cmd, cwd=project_dir)
        if not ok:
            return False, self._step(
                "compile_st",
                "failed",
                "ST compilation failed.",
                detail={"log": output, "bundle": str(bundle_path), "matiec_lib": matiec_lib_dir},
            )

        generated_artifacts = list(generated_c_dir.glob("*.c")) + list(generated_c_dir.glob("*.cc"))
        if not generated_artifacts:
            return False, self._step(
                "compile_st",
                "failed",
                "iec2c completed but generated no C artifacts.",
                detail={"bundle": str(bundle_path), "matiec_lib": matiec_lib_dir},
            )

        self._ensure_global_accessor_bindings(generated_c_dir)

        validation_errors = self._validate_generated_externals(
            project_dir,
            st_sources=st_files,
            allowed_registry=allowed_registry or set(),
            runtime_catalog=runtime_catalog or set(),
        )
        if validation_errors:
            first = validation_errors[0]
            return False, self._step(
                "compile_st",
                "failed",
                first.get("message", "Compile validation failed due to undeclared variables."),
                detail={
                    "error_code": first.get("error_code"),
                    "engineering_errors": validation_errors,
                },
            )

        return True, self._step(
            "compile_st",
            "passed",
            f"Compiled ST bundle with iec2c and produced {len(generated_artifacts)} C artifact(s).",
            detail={
                "bundle": str(bundle_path),
                "matiec_lib": matiec_lib_dir,
                "generated_c": [item.name for item in generated_artifacts[:20]],
            },
        )

    def generate_c(self, project_dir: Path) -> tuple[bool, dict[str, Any]]:
        generated_c_dir = project_dir / "generated_c"
        generated_c_dir.mkdir(parents=True, exist_ok=True)
        generated_candidates = sorted(generated_c_dir.glob("*.c")) + sorted(generated_c_dir.glob("*.cc"))
        if not generated_candidates:
            fallback_sources = sorted(project_dir.glob("*.c")) + sorted(project_dir.glob("*.cc"))
            for source in fallback_sources:
                source.replace(generated_c_dir / source.name)
            generated_candidates = sorted(generated_c_dir.glob("*.c")) + sorted(generated_c_dir.glob("*.cc"))

        if not generated_candidates:
            return False, self._step("generate_c", "failed", "No generated C artifacts were produced by iec2c.")

        moved = [item.name for item in generated_candidates]

        return True, self._step(
            "generate_c",
            "passed",
            f"Generated C artifacts prepared: {len(moved)} file(s).",
            detail={"generated_files": moved},
        )

    def build_runtime(self, project_dir: Path) -> tuple[bool, dict[str, Any]]:
        ok, output = self._run_cmd(["make", "clean"], cwd=project_dir, timeout_seconds=120)
        if not ok:
            self.logger.warning("runtime_engine make clean warning: %s", output)

        ok, output = self._run_cmd(["make", self.runtime_binary_name], cwd=project_dir, timeout_seconds=240)
        if not ok:
            return False, self._step("build_runtime", "failed", "Runtime build failed.", detail={"log": output})

        binary_path = project_dir / self.runtime_binary_name
        if not binary_path.exists():
            return False, self._step("build_runtime", "failed", f"Build completed but binary is missing at {binary_path}.")

        binary_path.chmod(0o755)
        return True, self._step(
            "build_runtime",
            "passed",
            f"Runtime binary built at {binary_path}.",
            detail={"runtime_binary": str(binary_path)},
        )

    def apply_io(self, project_dir: Path, io_map: list[dict[str, Any]]) -> tuple[bool, dict[str, Any]]:
        config_path = project_dir / "io_config.json"
        try:
            config_path.write_text(json.dumps({"io_points": io_map}, indent=2))
        except Exception as exc:
            return False, self._step("apply_io", "failed", f"Failed to write io_config.json: {exc}")
        return True, self._step(
            "apply_io",
            "passed",
            f"IO configuration written to {config_path} with {len(io_map)} point(s).",
            detail={"io_config": str(config_path), "io_points": len(io_map)},
        )

    def start_runtime(self, project_dir: Path) -> tuple[bool, dict[str, Any]]:
        runtime_binary = project_dir / self.runtime_binary_name
        if not runtime_binary.exists() or not os.access(runtime_binary, os.X_OK):
            return False, self._step(
                "start_runtime",
                "failed",
                f"Runtime binary not found/executable at {runtime_binary}.",
            )

        command = [str(runtime_binary)]

        if self._runtime_process and self._runtime_process.poll() is None:
            self.stop_runtime()

        try:
            self._runtime_process = subprocess.Popen(
                command,
                cwd=str(project_dir),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
                start_new_session=True,
            )
        except Exception as exc:
            return False, self._step("start_runtime", "failed", f"Failed to start runtime process {' '.join(command)}: {exc}")

        return True, self._step(
            "start_runtime",
            "passed",
            f"Runtime process started with command: {' '.join(command)}",
            detail={"pid": self._runtime_process.pid},
        )

    def stop_runtime(self) -> tuple[bool, dict[str, Any]]:
        if self._runtime_process and self._runtime_process.poll() is None:
            try:
                os.killpg(os.getpgid(self._runtime_process.pid), signal.SIGTERM)
            except Exception as exc:
                return False, self._step("stop_runtime", "failed", f"Failed to stop runtime process group: {exc}")
            return True, self._step("stop_runtime", "passed", "Runtime process stopped.")

        return False, self._step("stop_runtime", "failed", "No active runtime process is running.")

    def runtime_status(self) -> dict[str, Any]:
        running = bool(self._runtime_process and self._runtime_process.poll() is None)
        return {
            "status": "running" if running else "stopped",
            "project_dir": str(self._active_project_dir) if self._active_project_dir else None,
            "pid": self._runtime_process.pid if running and self._runtime_process else None,
            "runtime_binary": self.runtime_binary_name,
        }
