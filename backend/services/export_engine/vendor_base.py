from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from .common import LogicModel, VendorExportResult


class BaseVendorExporter(ABC):
    vendor_key: str

    @abstractmethod
    def export(self, output_root: Path, logic_model: LogicModel) -> VendorExportResult:
        raise NotImplementedError
