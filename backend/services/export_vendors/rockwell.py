from __future__ import annotations

from services.export_vendors.base import BaseVendorRenderer


class RockwellRenderer(BaseVendorRenderer):
    vendor_key = "rockwell"
    vendor_display_name = "Rockwell Studio 5000"
    template_name = "rockwell_l5x_project.j2"

    def output_filename(self, project_name: str) -> str:
        normalized = "_".join(part for part in project_name.strip().split() if part) or "project"
        return f"{normalized}.l5x"
