import pdfplumber
import re

def find_and_print_remaining_string(key_phrase, text):           #main string to find all the details using given key_phrase
    pattern = re.escape(key_phrase)
    pattern = r"\b{}\b".format(pattern)
    match = re.search(pattern, text, re.IGNORECASE)
    
    if match:
        remaining_string = text[match.end():].strip()
        return remaining_string
    else:
        index = text.lower().find(key_phrase.lower())
    
        if index != -1:
            remaining_string = text[index + len(key_phrase):].strip()
            return remaining_string
    
def search_pattern(string):                                        #for alphanumeric patterns like ID, invoice number etc.
    pattern = r"^.*?(?<=\d)(?=\s*[a-zA-Z])"
    match = re.search(pattern, string)
    if match:
        return match.group()
    else:
        return None
    
def check_pattern(string):                                         #for money related expression to check the validity 
    pattern = r"^\s*(?:INR|RS|₹)\s*.*?\d\s*$"
    match = re.match(pattern, string)
    if match:
        return True
    else:
        return False
    
def find_and_print_bank_info(bank_names, text_list):                         #for bank details of the vendor 

    pattern = r"(?i)(?<!\w){}(?!\w)".format("|".join(map(re.escape, bank_names)))
    regex = re.compile(pattern)
    
    for text in text_list:
        match = regex.search(text)
        
        if match:
            start_index = match.start()
            remaining_string = text[start_index:].strip()
            next_two_strings = text_list[text_list.index(text) + 1: text_list.index(text) + 3]
            
            print(remaining_string)
            for string in next_two_strings:
                print(string)
            print()

def remove_duplicates(text):
    words = re.findall(r'\b\w+\b', text)
    unique_words = []
    for word in words:
        if word not in unique_words:
            unique_words.append(word)
    updated_text = ' '.join(unique_words)
    return updated_text

def address_fn(key_words, text_list):                                       #this is to find the reciever's address in the code 
    pattern = r"\b(?:{})\b".format("|".join(map(re.escape, key_words)))
    regex = re.compile(pattern, re.IGNORECASE)
    found_start = False
    found_gstin = False
    address = []

    for text in text_list:
        match = regex.search(text)

        if match:
            found_start = True

        if found_start and "GSTIN" in text:
            found_gstin = True

        if found_start and not found_gstin:
            if not match:
                address.append(text.strip())

        if found_gstin:
            address.append(text.strip())
            break

    updated_address = remove_duplicates(' '.join(address))
    return updated_address

        

pdf_path = ''                                                               #add the file path here 

with pdfplumber.open(pdf_path) as pdf:
    page=pdf.pages[0]
    text=page.extract_text()

l=text.split("\n")

bank_names = ["HDFC Bank", "SBI", "ICICI", "KOTAK",] 
key_words = ["bill to", "ship to"]

print("-"*50)
print("                 Invoice Details")
print("-"*50)
print(" ")
print("Billing Address: ")
address=address_fn(key_words,l)
print(address)
print(" ")
for i in l:
    a=find_and_print_remaining_string("#",i)
 
    if a != None:
        result = search_pattern(a)
        if result:
            print("Invoice No.           ",result)
            print(" ")


for i in l:
    a=find_and_print_remaining_string("Invoice date",i)
    if a != None:
        print("Invoice Date          ",a)
        print(" ")


for i in l:
    a=find_and_print_remaining_string("Due date",i)
    if a != None:
        print("Due Date              ",a)
        print(" ")


for i in l:
    a=find_and_print_remaining_string("Total",i)
    if a != None:
        result = check_pattern(a)
        if result:
            print("Total                  :",a)
            print(" ")



for i in l:
    a=find_and_print_remaining_string("balance due",i)
    if a != None:
        print("Balance Due            :",a)
        print(" ")

    
print(" ")
print("The bank details : ")

find_and_print_bank_info(bank_names,l)

for i in l:
    a=find_and_print_remaining_string("Dear",i)
    
    if a != None:
        a.lstrip(" ")
        print("Reciepent's Name        :",a)

for i in l:
    a=find_and_print_remaining_string("Registration ID",i)
    if a != None:
        result = search_pattern(a)
        if result:
            print("Registration ID         :",result)
        

for i in l:
    a=find_and_print_remaining_string("Registration Fee",i)
    if a != None:
        result = search_pattern(a)
        if result:
            result_2 = check_pattern(result)
            if result_2:
                print("Registration Fee        :",result)
        

for i in l:
    a=find_and_print_remaining_string("Registration Date/time",i)
    if a != None:
        a.lstrip(" ")
        print("Registeration Date/time :",a)
        
print("-"*50)
