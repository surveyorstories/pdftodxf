# -*- coding: utf-8 -*-

from qgis.core import QgsProcessingProvider
from .pdf_to_dxf_algorithm import PdfToDxfAlgorithm
from qgis.PyQt.QtGui import QIcon

class PdfToDxfProvider(QgsProcessingProvider):

    def loadAlgorithms(self):
        self.addAlgorithm(PdfToDxfAlgorithm())

    def id(self):
        return 'pdftodxf'

    def name(self):
        return 'Bhukamatha-lite'

    def icon(self):
        return QIcon()

    def longName(self):
        return self.name()
