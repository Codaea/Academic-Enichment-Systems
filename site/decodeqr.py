import io
from pdf2image import convert_from_path
from pyzbar import pyzbar
from PIL import Image
import time


def start_benchmark():
    global start_time
    start_time = time.time()


def stop_benchmark():
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Execution time: {execution_time} seconds")




def pdf_to_images(pdf_path):
    images = convert_from_path(pdf_path)
    return images

def decode_qr_codes(images):
    qr_codes = []
    for image in images:
        # Convert the image to grayscale
        image = image.convert("L")
        # Decode the QR codes in the image
        decoded_objects = pyzbar.decode(image)
        for obj in decoded_objects:
            qr_code = obj.data.decode("utf-8")
            qr_codes.append(qr_code)
    return qr_codes




pdf_path = r"C:/Users/dakot/Documents/GitHub/CghsAE/Requests.pdf"





# run 
start_benchmark()
images = pdf_to_images(pdf_path)
stop_benchmark()
start_benchmark()
qr_codes = decode_qr_codes(images)
stop_benchmark()
print(qr_codes)