from services.export_vendors.base import BaseVendorRenderer
from services.export_vendors.rockwell import RockwellRenderer
from services.export_vendors.siemens import SiemensRenderer


class CodesysRenderer(BaseVendorRenderer):
    vendor_key = "codesys"
    vendor_display_name = "Codesys"


class BeckhoffRenderer(BaseVendorRenderer):
    vendor_key = "beckhoff"
    vendor_display_name = "TwinCAT"


class OpenPLCRenderer(BaseVendorRenderer):
    vendor_key = "openplc"
    vendor_display_name = "OpenPLC"


VENDOR_RENDERERS = {
    "siemens": SiemensRenderer(),
    "rockwell": RockwellRenderer(),
    "codesys": CodesysRenderer(),
    "beckhoff": BeckhoffRenderer(),
    "openplc": OpenPLCRenderer(),
}


def get_renderer(vendor: str) -> BaseVendorRenderer | None:
    return VENDOR_RENDERERS.get(vendor.lower())
