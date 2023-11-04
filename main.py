import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from fastapi.responses import JSONResponse
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from tqdm import tqdm
from typing import List  # Import List from typing module

app = FastAPI()

from PIL import Image

def convert_images_to_pdf(image_path: str, output_pdf_path: str):
    if not image_path:
        # If there are no image paths provided, raise an error or handle it as per your application's requirements
        raise ValueError("No image paths provided to convert to PDF.")

    images = []
    try:
        img = Image.open(image_path)
        # Convert to RGB if the image is in a mode that is not supported in PDF (like 'P' mode)
        if img.mode in ['RGBA', 'LA', 'P']:
            img = img.convert('RGB')
        images.append(img)
    except Exception as e:
        # Handle exceptions if an image cannot be opened
        raise ValueError(f"Could not open image {image_path}: {e}")

    if images:
        images[0].save(output_pdf_path, "PDF", resolution=100.0, save_all=True, append_images=images[1:])
    else:
        # If for some reason all images failed to load, handle it accordingly
        raise ValueError("No images were loaded to convert to PDF.")

def process_pdf(pdf_path: str):
    # Construct the paddleocr command
    cmd = f"paddleocr --image_dir='{pdf_path}' --type=structure --recovery=true --use_pdf2docx_api=true --lang='en'"
    
    # Run the command using subprocess
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Check if the process was successful
    if result.returncode == 0:
        return True
    else:
        return False

def cleanup():
    pdf_folder = Path("pdfs")
    output_folder = Path("output")
    
    # Delete the 'pdfs' folder and its contents
    if pdf_folder.exists():
        shutil.rmtree(pdf_folder)
    
    # Delete the 'output' folder and its contents
    if output_folder.exists():
        shutil.rmtree(output_folder)

@app.post("/uploads/")
async def upload_files(files: List[UploadFile] = File(...)):
    output_zip_path = os.path.join("./", "output.zip")
    pdf_folder = Path("pdfs")
    pdf_folder.mkdir(parents=True, exist_ok=True)
    output_folder = Path("output")
    output_folder.mkdir(parents=True, exist_ok=True)

    for file in tqdm(files, desc="Processing Files"):
        # Check file type
        if file.filename.lower().endswith('.pdf'):
            file_path = pdf_folder / file.filename
            with file_path.open("wb") as pdf_file:
                pdf_file.write(file.file.read())

            pdf_path = str(pdf_folder / file.filename)
            # Process the uploaded PDF
            success = process_pdf(pdf_path)

            if not success:
                cleanup()
                return JSONResponse(content={"error": f"Failed to process {file.filename}"}, status_code=500)
            
        elif file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.PNG', '.JPG', 'JPEG')):
            # Convert images to PDF if there are any
            filerename = f"{file.filename[:-4]}.pdf"
            image_path = pdf_folder / file.filename
            pdf_path = pdf_folder / filerename

            with image_path.open("wb") as image_file:
                image_file.write(file.file.read())

            convert_images_to_pdf(image_path, str(pdf_path))
 
            with pdf_path.open("wb") as pdf_file:
                pdf_file.write(file.file.read())

            pdf_path = str(pdf_folder / file.filename)
            # Process the uploaded PDF
            success = process_pdf(pdf_path)
  
        else:
            cleanup()
            return JSONResponse(content={"error": "Only PDF and image files are allowed"}, status_code=400)

    # Create a ZIP file containing the processed output
    shutil.make_archive(output_zip_path[:-4], 'zip', output_folder)
    cleanup()
    return FileResponse(output_zip_path, headers={"Content-Disposition": "attachment; filename=output.zip"})
