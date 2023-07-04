# It is using PyOCR and PyPDF2 and openai

import openai
import PyPDF2
from pdf2image import convert_from_path
import pytesseract
import os
import pyocr
import pyocr.builders
from PIL import Image
import re
import cv2
pytesseract.pytesseract.tesseract_cmd = r"/usr/local/Cellar/tesseract/5.3.1_1/bin/tesseract"
openai.api_key = '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'
tools = pyocr.get_available_tools()
if len(tools) == 0:
    print("No OCR tool found. Please install Tesseract.")
    exit(1)
tool = tools[0]




# path = "lazzez.jpeg"
# path = "makemytrip1.pdf"
# path = 'goibibo1.pdf'
# path = 'goibibo3.pdf'
# path = 'sample1.pdf'
# path = 'makemytrip2.pdf'
# path = 'Non-Hotel/Uber.pdf' # Non-Hotel Bill
# path = 'Non-Hotel/AirTickets.pdf' # Non-Hotel Bill
# path = "La2.png" # Upside Down Image

# path = 'Non-Hotel/Uber_ro.pdf'
path = 'Non-Hotel/porter.pdf'
# path = 'Non-Hotel/ola.pdf'
# path = 'Non-Hotel/ola2.pdf'






def rotate_image(image_path, angle):
    # Load the image using OpenCV
    image = cv2.imread(image_path)

    # Get the image height, width, and channels
    height, width, channels = image.shape

    # Compute the rotation matrix
    rotation_matrix = cv2.getRotationMatrix2D((width/2, height/2), angle, 1)

    # Apply the rotation to the image
    rotated_image = cv2.warpAffine(image, rotation_matrix, (width, height))

    return rotated_image

def save_image(image, output_path):
    # Save the image to the specified output path
    cv2.imwrite(output_path, image)

def extract_text_from_pdf_pypdf2(file_path):
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ''
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += "\n"
            text += page.extract_text()
        return text

def extract_text_from_pdf(pdf_path):
    images = convert_from_path(pdf_path)

    text = ""
    for i, image in enumerate(images):
        image = image.convert("RGB")
        image.save(f"temp_{i}.jpg", "JPEG")
        path1 = rotate_the_image(f"temp_{i}.jpg")
        text += tool.image_to_string(
        Image.open(path1),
        lang='eng', 
        builder=pyocr.builders.TextBuilder()
    )

    for i in range(len(images)):
        temp_image_path = f"temp_{i}.jpg"
        os.remove(temp_image_path)

    return text

def rotate_the_image(path):
    image = Image.open(path)
    output = pytesseract.image_to_osd(image, config=" — psm 0")

    angle = re.search(r"Orientation in degrees: \d+", output).group().split(":")[-1].strip()
    confidence= float(re.search(r"Orientation confidence: \d+\.\d+", output).group().split(":")[-1].strip())

    if confidence>2.0:
        rotated_image = rotate_image(path,int(angle))
        # Save the rotated image
        output_path = './rotated_image.jpg'
        save_image(rotated_image, output_path)
        path = output_path
    return path


if path.endswith('.pdf'):
    is_pdf = True
else:
    is_pdf = False

if is_pdf:
    # text = extract_text_from_pdf(path) # Using pyOCR with PDFs
    text = extract_text_from_pdf_pypdf2(path)

else:
    rotate_the_image(path)
    image = Image.open(path)
    text = tool.image_to_string(
        image,
        lang='eng', 
        builder=pyocr.builders.TextBuilder())


# print('===========Testing Start===========')
# print(text)
# print('===========Testing End===========')
# exit()



def chat_with_gpt(prompt):
    response = openai.Completion.create(
        engine='text-davinci-003',  # Specify the ChatGPT model
        prompt=prompt,
        max_tokens=300,  # Adjust the value based on your desired response length
        temperature=0.6,  # Adjust the value to control the randomness of the response
        n=1,  # Generate a single response
        stop=None,  # You can specify a stopping condition if needed
        timeout=None,  # You can set a timeout if desired
    )
    return response.choices[0].text.strip()

# If you find some facts that relates to hotel bills then reply with "YES" else in any other case reply with "NO". 
# Give reasons for your answer. if no then what facts does it realtes with the hotel bill.
user_prompt1 = f"""Given a Bill OCR info, State if the bill is of Hotel Accommodation Stay category while sorting the bills of dierrent types such as Travel, Conference organizers, Random like stationary items for Automatic reimbuersment project.
You might wanna see if there are Room Details, Check-in/Check-out Date. If any of these are present then reply with "YES" else in any other case reply with "NO". 

Bill details:
`{text}`"""
response1 = chat_with_gpt(user_prompt1)
# response1 = " "
# print("--------------")
# print(response1)
print("--------------")

if "yes" in response1.lower():
    print("It is an accommodation bill, Extracting the details:\n")
    # exit()
else:
    print("Not an accommodation bill")
    print('Exiting...')
    exit()



user_prompt2 = f"""Title: Hotel Bill OCR Data Extraction

Prompt:
You are tasked with developing an OCR data extraction system for hotel bills in PDF format. The system should extract important information necessary for the reimbursement process from a college. The extracted details should be presented in CSV format for easy analysis. Your prompt should fetch the following essential details from the hotel bill:

1. Hotel Name: [Hotel Name]
2. Address: [Hotel Address]
3. Bill number/Invoice number: [Bill Number]
4. booking ID / Confirmation ID / Booking #: [Booking ID]
5. Check-in Date and Time: [Check-in Date Time]
6. Check-out Date and Time: [Check-out Date Time]
7. Total Amount: [Total Amount Charged]
8. Booking platform: [Booking Platform]
9. Bill date: [Bill Date]

Ensure that the system accurately extracts the above information from the OCR text of the hotel bill and presents it in a well-format. GIVE ONLY THE EXTRACTED DETAILS. NO OTHER RESPONSE SHOULD BE PRESENT IN THE REPLY.
Here is the OCR text: {text}"""


response = chat_with_gpt(user_prompt2)
print("--------------")
print(response)
print("--------------")

