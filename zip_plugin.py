import shutil
import os

def zip_plugin():
    # Name of the directory to zip
    source_dir = "PDFtoDXF"
    # Output zip file name (without extension)
    output_filename = "PDFtoDXF"
    
    # Create zip
    shutil.make_archive(output_filename, 'zip', root_dir='.', base_dir=source_dir)
    print(f"Created {output_filename}.zip")

if __name__ == "__main__":
    zip_plugin()
