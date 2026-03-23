from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment


@dataclass(frozen=True)
class VendorRenderResult:
    vendor: str
    files: dict[str, str]


class BaseVendorRenderer:
    vendor_key: str = "base"
    vendor_display_name: str = "Generic Vendor"
    template_name: str = "generic_project.j2"

    def build_context(self, logic_model: dict[str, Any]) -> dict[str, Any]:
        return {
            "vendor": self.vendor_display_name,
            "project": logic_model.get("project", {}),
            "summary": logic_model.get("summary", {}),
            "units": logic_model.get("units", []),
            "source_files": logic_model.get("source_files", []),
        }

    def output_filename(self, project_name: str) -> str:
        normalized = "_".join(part for part in project_name.strip().split() if part) or "project"
        return f"{normalized}_{self.vendor_key}_project.txt"

    def extra_files(self, logic_model: dict[str, Any]) -> dict[str, str]:
        return {
            "README.txt": (
                f"Vendor export generated for {self.vendor_display_name}.\\n"
                "This output was generated from vendor-agnostic Structured Text artifacts.\\n"
            )
        }

    def render_project(
        self,
        logic_model: dict[str, Any],
        output_root: Path,
        jinja_env: Environment,
    ) -> dict[str, Any]:
        context = self.build_context(logic_model)
        template = jinja_env.get_template(self.template_name)
        rendered = template.render(**context)

        project_name = str((logic_model.get("project") or {}).get("name") or "project")
        main_output = self.output_filename(project_name)

        generated: dict[str, str] = {main_output: rendered}
        generated.update(self.extra_files(logic_model))

        for relative_path, contents in generated.items():
            target = output_root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(contents, encoding="utf-8")

        return {
            "files": sorted(generated.keys()),
            "metadata": {},
        }
