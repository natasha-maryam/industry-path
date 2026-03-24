from __future__ import annotations

from .beckhoff.exporter import BeckhoffExporter
from .codesys.exporter import CodesysExporter
from .openplc.exporter import OpenPLCExporter
from .rockwell.exporter import RockwellExporter
from .siemens.exporter import SiemensExporter
from .vendor_base import BaseVendorExporter


VENDOR_EXPORTERS: dict[str, BaseVendorExporter] = {
    "siemens": SiemensExporter(),
    "rockwell": RockwellExporter(),
    "codesys": CodesysExporter(),
    "beckhoff": BeckhoffExporter(),
    "openplc": OpenPLCExporter(),
}


def get_vendor_exporter(vendor: str) -> BaseVendorExporter | None:
    return VENDOR_EXPORTERS.get(vendor.lower())
