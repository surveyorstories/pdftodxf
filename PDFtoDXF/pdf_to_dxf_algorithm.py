# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFileDestination,
                       QgsProcessingParameterBoolean,
                       QgsProcessingException,
                       QgsProcessingContext,
                       QgsMessageLog,
                       Qgis)
import sys
import os

# --- Dependency Handling ---
# --- Dependency Handling ---
MISSING_DEPS = []

try:
    import fitz
except ImportError:
    MISSING_DEPS.append('pymupdf')

try:
    import ezdxf
except ImportError:
    MISSING_DEPS.append('ezdxf')

class PdfToDxfAlgorithm(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'

    LOAD_OUTPUT = 'LOAD_OUTPUT'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return PdfToDxfAlgorithm()

    def name(self):
        return 'pdftodxf_algo'

    def displayName(self):
        return self.tr('PDF to DXF Converter')

    def group(self):
        return 

    def groupId(self):
        return 

    def shortHelpString(self):
        return self.tr("Converts a PDF file to a DXF file using PyMuPDF and ezdxf.\n"
        "Please install them using the OSGeo4W Shell:\n"
                        """1. Open 'OSGeo4W Shell' from your Start Menu.\n
                        2. Run: pip install pymupdf "ezdxf&lt;1.1"\n
                        3. Restart QGIS.""")

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT,
                self.tr('Input PDF'),
                behavior=QgsProcessingParameterFile.File,
                fileFilter='PDF Files (*.pdf)'
            )
        )

        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT,
                self.tr('Output DXF'),
                fileFilter='DXF Files (*.dxf)'
            )
        )
        
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.LOAD_OUTPUT,
                self.tr('Load output into project'),
                defaultValue=False
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        if MISSING_DEPS:
             raise QgsProcessingException(
                self.tr(f"Missing dependencies: {', '.join(MISSING_DEPS)}.\n\n"
                        """ Please install them using the OSGeo4W Shell:\n
                        1. Open 'OSGeo4W Shell' from your Start Menu.\n
                        2. Run: pip install pymupdf "ezdxf&lt;1.1" \n
                        3. Restart QGIS.""")
            )

        source_path = self.parameterAsFile(parameters, self.INPUT, context)
        output_path = self.parameterAsString(parameters, self.OUTPUT, context)
        load_output = self.parameterAsBool(parameters, self.LOAD_OUTPUT, context)

        if not source_path:
            raise QgsProcessingException(self.tr('Invalid input PDF.'))
        
        if not output_path:
             raise QgsProcessingException(self.tr('Invalid output path.'))

        feedback.pushInfo(f"Converting {source_path} to {output_path}...")

        try:
            import fitz
            import ezdxf
            generated_files = self.convert_pdf_to_dxf(source_path, output_path, fitz, ezdxf)
            
            if load_output:
                # Load layers into project
                for file_path in generated_files:
                    context.addLayerToLoadOnCompletion(
                        file_path,
                        QgsProcessingContext.LayerDetails(os.path.basename(file_path), context.project(), self.OUTPUT)
                    )
                
            feedback.pushInfo(f"Successfully converted. Generated {len(generated_files)} file(s).")
        except Exception as e:
            QgsMessageLog.logMessage(f"PDF2DXF Error: {str(e)}", "PDF2DXF", Qgis.Critical)
            raise QgsProcessingException(self.tr(f"Conversion failed: {e}"))

        return {self.OUTPUT: output_path}

    def convert_pdf_to_dxf(self, pdf_path, dxf_path, fitz, ezdxf):
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
        doc = fitz.open(pdf_path)
        generated_files = []
        
        # If multiple pages, save separate files
        if len(doc) > 1:
            base, ext = os.path.splitext(dxf_path)
            for page_num in range(len(doc)):
                dxf = ezdxf.new()
                # Create layers
                dxf.layers.new(name='PDF_GEOMETRY', dxfattribs={'color': 7})
                dxf.layers.new(name='PDF_TEXT', dxfattribs={'color': 1})
                
                msp = dxf.modelspace()
                
                page = doc[page_num]
                self._convert_single_page(page, msp)
                
                page_output_path = f"{base}_page_{page_num + 1}{ext}"
                dxf.saveas(page_output_path)
                generated_files.append(page_output_path)
        else:
            # Single page
            dxf = ezdxf.new()
            # Create layers
            dxf.layers.new(name='PDF_GEOMETRY', dxfattribs={'color': 7})
            dxf.layers.new(name='PDF_TEXT', dxfattribs={'color': 1})
            
            msp = dxf.modelspace()
            if len(doc) > 0:
                self._convert_single_page(doc[0], msp)
            dxf.saveas(dxf_path)
            generated_files.append(dxf_path)
            
        return generated_files

    def _convert_single_page(self, page, msp):
        # 1. Extract Drawings
        paths = page.get_drawings()
        page_height = page.rect.height
        
        for path in paths:
            for item in path["items"]:
                cmd = item[0]
                if cmd == "l":
                    p1 = item[1]
                    p2 = item[2]
                    msp.add_line(
                        self._transform_point(p1, 0, page_height),
                        self._transform_point(p2, 0, page_height),
                        dxfattribs={'layer': 'PDF_GEOMETRY'}
                    )
                elif cmd == "c":
                    p1 = item[1]
                    p2 = item[2]
                    p3 = item[3]
                    p4 = item[4]
                    control_points = [
                        self._transform_point(p1, 0, page_height),
                        self._transform_point(p2, 0, page_height),
                        self._transform_point(p3, 0, page_height),
                        self._transform_point(p4, 0, page_height)
                    ]
                    msp.add_spline(control_points, degree=3, dxfattribs={'layer': 'PDF_GEOMETRY'})
                elif cmd == "re":
                    rect = item[1]
                    p1 = (rect.x0, rect.y0)
                    p2 = (rect.x1, rect.y0)
                    p3 = (rect.x1, rect.y1)
                    p4 = (rect.x0, rect.y1)
                    points = [p1, p2, p3, p4, p1]
                    dxf_points = [self._transform_point(p, 0, page_height) for p in points]
                    msp.add_lwpolyline(dxf_points, dxfattribs={'layer': 'PDF_GEOMETRY'})

        # 2. Extract Text
        text_dict = page.get_text("dict")
        text_count = 0
        for block in text_dict.get("blocks", []):
            if block["type"] == 0: # Text block
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"]
                        if not text.strip():
                            continue
                        
                        text_count += 1
                        size = span["size"]
                        origin = span["origin"]
                        insert_point = self._transform_point(origin, 0, page_height)
                        
                        msp.add_mtext(
                            text,
                            dxfattribs={
                                'char_height': size,
                                'insert': insert_point,
                                'attachment_point': 7, # BottomLeft
                                'layer': 'PDF_TEXT'
                            }
                        )
        
        QgsMessageLog.logMessage(f"PDF2DXF: Found {text_count} text objects on page.", "PDF2DXF", Qgis.Info)

    def _transform_point(self, point, x_offset, page_height):
        x, y = point[0], point[1]
        new_y = page_height - y
        return (x + x_offset, new_y)
