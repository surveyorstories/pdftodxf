# -*- coding: utf-8 -*-

from qgis.core import QgsApplication
from .pdf_to_dxf_provider import PdfToDxfProvider

class PdfToDxfPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.provider = None

    def initGui(self):
        self.provider = PdfToDxfProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)
        
        # Check dependencies on startup
        from . import dependencies
        dependencies.install_deps(self.iface)

    def unload(self):
        if self.provider:
            try:
                QgsApplication.processingRegistry().removeProvider(self.provider)
            except RuntimeError:
                # Provider C++ object might already be deleted
                pass
            self.provider = None
