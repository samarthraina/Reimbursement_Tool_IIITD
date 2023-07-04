import PyPDF2
import re

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            text += page_text
    return text

def extract_information_from_pdf(pdf_text):
    extracted_info = {}

    # Convert text to lowercase
    pdf_text = pdf_text.lower()

    # Extract date using regex pattern
    date_match = re.search(r"(\d{1,2}\s[a-z]+\s\d{4})", pdf_text)
    if date_match:
        extracted_info["Date"] = date_match.group(1)

    # Extract name using regex pattern
    name_match = re.search(r"(?i)name:(.*)", pdf_text)
    if name_match:
        extracted_info["Name"] = name_match.group(1).strip()

    # Extract PNR using regex pattern
    pnr_match = re.search(r"pnr:? ([a-z0-9]+)", pdf_text)
    if pnr_match:
        extracted_info["PNR"] = pnr_match.group(1)

    # Extract origin using regex pattern
    origin_match = re.search(r"origin:? ([a-z\s]+)", pdf_text)
    if origin_match:
        extracted_info["Origin"] = origin_match.group(1)

    # Extract destination using regex pattern
    destination_match = re.search(r"destination:? ([a-z\s]+)", pdf_text)
    if destination_match:
        extracted_info["Destination"] = destination_match.group(1)

    # Extract arrival and departure times using regex patterns
    time_match = re.findall(r"(\d{1,2}:\d{2})", pdf_text)
    if len(time_match) >= 1:
        extracted_info["Arrival Time"] = time_match[0]
    if len(time_match) >= 2:
        extracted_info["Departure Time"] = time_match[1]

    # Extract address using regex pattern
    address_match = re.search(r"(?i)address:? (.+)", pdf_text)
    if address_match:
        extracted_info["Address"] = address_match.group(1)

    return extracted_info

# Example usage
pdf_file = r"DEL-Airport-Home-03 May 2023.pdf"

# Extract text from PDF
extracted_text = extract_text_from_pdf(pdf_file)

# Extract information from the extracted text
extracted_info = extract_information_from_pdf(extracted_text)

# Copy the extracted information
copied_data = ""
for key, value in extracted_info.items():
    copied_data += f"{key}: {value}\n"

# Print the extracted information
print(copied_data)
