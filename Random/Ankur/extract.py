import argparse
import json
import os
import pprint
import tkinter as tk
import typing
from decimal import Decimal
from tkinter import filedialog

import pytesseract
from borb.pdf.canvas.geometry.rectangle import Rectangle
from borb.pdf.document.document import Document
from borb.pdf.pdf import PDF
from borb.toolkit.location.location_filter import LocationFilter
from borb.toolkit.text.simple_text_extraction import SimpleTextExtraction
from PIL import Image

import parse

# from temp import ResizeWithAspectRatio

DPI = 600
EXACT_FIELD_MIN_CONF = 90


def process_pdf(file, dest):
    os.system(f"magick convert -density {DPI} {file} -quality 100 {dest}")
    # or possibly ./textcleaner.sh -g -e none -f 15 -D 300 invoice.pdf out.tif
    return dest


def get_exact_text(data, i, image_w, image_h, filename):
    (x, y, w, h) = (
        data["left"][i],
        data["top"][i],
        data["width"][i],
        data["height"][i],
    )
    (x0, y0, x1, y1) = (x, y, x + w, y + h)

    d: typing.Optional[Document] = None

    with open(filename, "rb") as pdf_in_handle:
        d = PDF.loads(pdf_in_handle)
        pdf_w = d.get_page(0).get_page_info().get_width()
        pdf_h = d.get_page(0).get_page_info().get_height()

    # Define rectangle of interest
    # x, y, width, height
    # Change y coordinate's reference point
    y0 = image_h - y0
    y1 = image_h - y1

    # Scale coordinates from H and W to h and w
    x0, y0, x1, y1 = (
        x0 * pdf_w / image_w,
        y0 * pdf_h / image_h,
        x1 * pdf_w / image_w,
        y1 * pdf_h / image_h,
    )
    width = x1 - x0
    height = y0 - y1

    # Apply some padding to the sides
    PADDING_X = Decimal(0.10)  # 10% of given width
    PADDING_Y = Decimal(0)  # 1% of given height

    width = (1 + PADDING_X) * width
    height = (1 + PADDING_Y) * height

    x0 = x0 - PADDING_X / 2 * width
    y0 = y0 - PADDING_Y / 2 * height

    r: Rectangle = Rectangle(
        Decimal(x0),  # lower_left_x),
        Decimal(y1),  # lower_left_y),
        Decimal(x1 - x0),  # width),
        Decimal(y0 - y1),
    )  # height),

    # Set up EventListener(s)
    l0: LocationFilter = LocationFilter(r)
    l1: SimpleTextExtraction = SimpleTextExtraction()
    l0.add_listener(l1)

    with open(filename, "rb") as pdf_in_handle:
        d = PDF.loads(pdf_in_handle, [l0])

    assert d is not None
    return l1.get_text()[0]


def extract(args):
    """Extract information from the given input receipt image or PDF file.

    Args:
        args (argparse.Namespace): The command line arguments:
            filename (str): The path to the input file.
            dest (str): The path to the output file.
            -l/--log (bool): Whether to print log messages.

    Returns: The information extracted.
    """
    if args.filename:
        filename = args.filename
        if args.log:
            print("Given file:", filename)
    else:
        root = tk.Tk()
        root.withdraw()
        filename = filedialog.askopenfilename(
            title="Select a file to be processed",
            filetypes=(
                ("PDF files", "*.pdf"),
                ("Images", "*.jpeg *.jpg *.tif *.tiff *.png"),
            ),
        )
        root.destroy()

    # If this is a PDF file, convert it to an image
    originally_pdf = filename if filename.endswith(".pdf") else False
    if originally_pdf:
        if args.log:
            print("Converting PDF to image...")
        dest = process_pdf(filename, "temp.png")
        filename = os.path.join(os.getcwd(), dest)
        if args.log:
            print("Converted PDF to image:", filename)

    if args.log:
        print("Processing image:", filename)

    img = Image.open(filename)
    width, height = img.size
    img.close()
    data = pytesseract.image_to_data(
        filename, output_type=pytesseract.Output.DICT, lang="script/Devanagari"
    )
    with open("temp.josn", "w") as f:
        json.dump(data, f, indent=4)
    n_boxes = len(data["level"])
    text = ""

    # import cv2
    # img = cv2.imread(filename)
    for i in range(n_boxes):
        partial_text, conf = data["text"][i], data["conf"][i]
        x, y, w, h = (
            data["left"][i],
            data["top"][i],
            data["width"][i],
            data["height"][i],
        )
        if partial_text:
            last_was_space = (not text) or (text and text[-1].isspace())
            if not partial_text.isspace():
                text += ("" if last_was_space else " ") + partial_text
        elif text and not text[-2:].isspace():
            text += "\n"
        # color = (36,255,12) if conf != -1 else (200, 200, 200)
        # cv2.putText(img, f"{text} ({conf})", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 1.4, color, 2)
        # cv2.rectangle(img, (x,y), (x+w,y+h) , color, 2)
    # resize = ResizeWithAspectRatio(img, height=1500)
    # cv2.imshow('img',resize)
    # cv2.waitKey(0)
    # os.system(
    #     f"tesseract {filename} {filename.replace('.', '_')}"
    #     + (" -c tessedit_write_images=true" if args.log else "")
    # )
    if args.log:
        print("Processing complete")

    if originally_pdf:
        os.remove("temp.png")

    # with open(filename.replace(".", "_") + ".txt", "r") as file:
    #     text = file.read()

    if args.log:
        print("Extracted text:", text)

    # if not args.log:
    #     os.remove(filename.replace(".", "_") + ".txt")

    if args.log:
        print("Parsing text...")

    information = parse.parse(text, parse.Sources.Bing)

    if args.log:
        print("Parsed:")
        print(information)

    # Get exact field confidences
    if information["seller_details"]["tax_number"]:
        tax_type = tuple(information["seller_details"]["tax_number"].keys())[0]
        tax_number = tuple(information["seller_details"]["tax_number"].values())[0]
    else:
        tax_type = None
        tax_number = None
    pan_number = information["seller_details"]["pan_number"]
    invoice_number = information["uids"]["Invoice No."]

    tax_number_box_index = pan_number_box_index = invoice_number_box_index = None
    for i in range(n_boxes):
        if data["text"][i] == tax_number:
            tax_number_box_index = i
        elif data["text"][i] == pan_number:
            pan_number_box_index = i
        elif data["text"][i] == invoice_number:
            invoice_number_box_index = i
        if (
            tax_number_box_index
            and pan_number_box_index
            and invoice_number_box_index
        ):
            break

    if tax_number_box_index:
        tax_number_conf = data["conf"][tax_number_box_index]
    else:
        tax_number_conf = -1
    if pan_number_box_index:
        pan_number_conf = data["conf"][pan_number_box_index]
    else:
        pan_number_conf = -1
    if invoice_number_box_index:
        invoice_number_conf = data["conf"][invoice_number_box_index]
    else:
        invoice_number_conf = -1
    
    confidence = {
        "tax_number": tax_number_conf,
        "pan_number": pan_number_conf,
        "invoice_number": invoice_number_conf,
    }
    if originally_pdf:
        if tax_number_box_index and (
            ("gst_number" == tax_type and len(tax_number) != 15)
            or tax_number_conf < EXACT_FIELD_MIN_CONF
        ):
            exact_text = get_exact_text(
                data, tax_number_box_index, width, height, originally_pdf
            )
            if exact_text and (
                ("gst_number" != tax_type)
                or ("gst_number" == tax_type and len(exact_text) == 15)
            ):
                information["seller_details"]["tax_number"][tax_type] = exact_text
                confidence["tax_number"] = 'EXTRACTED'
        if pan_number_box_index and (
            pan_number_conf < EXACT_FIELD_MIN_CONF or len(pan_number) != 10
        ):
            exact_text = get_exact_text(
                data, pan_number_box_index, width, height, originally_pdf
            )
            if exact_text and len(exact_text) == 10:
                information["seller_details"]["pan_number"] = exact_text
                confidence["pan_number"] = 'EXTRACTED'
        if invoice_number_box_index and (invoice_number_conf < EXACT_FIELD_MIN_CONF):
            exact_text = get_exact_text(
                data, invoice_number_box_index, width, height, originally_pdf
            )
            if exact_text:
                information["uids"]["Invoice No."] = exact_text
                confidence["invoice_number"] = 'EXTRACTED'

    if args.dest:
        with open(args.dest + ".json", "w") as file:
            json.dump(information, file, indent=4)
    return information, confidence


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract text from an image or PDF file using Tesseract OCR"
    )
    parser.add_argument("filename", nargs="?")
    parser.add_argument("dest", nargs="?")
    parser.add_argument("-l", "--log", action="store_true")
    args = parser.parse_args()

    information, confidence = extract(args)
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(information)
    pp.pprint(confidence)
