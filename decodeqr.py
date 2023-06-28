import io
import fitz
from pyzbar import pyzbar
from PIL import Image
import time


def start_benchmark():
    start_time = time.time()


def stop_benchmark():
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Execution time: {execution_time} seconds")




def decode_qr_codes_from_pdf(pdf_path):
    qr_codes = []
    doc = fitz.open(pdf_path)
    for page in doc:
        image_list = page.get_pixmap()
        img = Image.frombytes("RGB", (image_list.width, image_list.height), image_list.samples)
        decoded_objects = pyzbar.decode(img)
        for obj in decoded_objects:
            qr_code = obj.data.decode("utf-8")
            qr_codes.append(qr_code)
    doc.close()
    return qr_codes



pdf_path = r"C:/Users/dakot/Documents/GitHub/CghsAE/Requests.pdf"

# run 
start_benchmark()
qr_codes = decode_qr_codes_from_pdf(pdf_path)
stop_benchmark()
