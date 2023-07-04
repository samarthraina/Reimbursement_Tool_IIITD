import ast
import asyncio
import json
import re
from enum import Enum, auto

import openai
from EdgeGPT.EdgeGPT import Chatbot, ConversationStyle


class Sources(Enum):
    OpenAI = (auto(),)
    Bing = auto()


with open("schema.json", "r") as file:
    SCHEMA = file.read()
query = """Please extract information (uids, total, tax, name, currency, date, seller_details, summary) from the Tesseract-processed text given at the last. Give the output while very strictly following the given JSON schema. Use null for fields you could not find. Clearly separate the JSON output using a json-labelled codeblock enclosed with ``` on both sides.
This is the JSON schema:
```json
%s
```
This is the Tesseract-processed text:
```
%s
```
Try to evaluate mathematical expressions in the numerical fields if used.
"""
query = query % (SCHEMA, "%s")

SCHEMA_JSON = json.loads(SCHEMA)


def openai(query):
    # Set up OpenAI API credentials
    openai.api_key = "YOUR_API_KEY"

    # Generate a response from ChatGPT
    response = openai.Completion.create(
        engine="gpt-3.5-turbo",
        prompt=query,
        max_tokens=100,
        n=1,
        stop=None,
        temperature=0.7,
    )

    # Extract and return the answer from the response
    answer = response.choices[0].text.strip()
    return answer


async def bing(query):
    with open("bing_cookies_ankur.json", "r") as file:
        cookies = json.load(file)

    bot = await Chatbot.create(
        cookies=cookies
    )  # Passing cookies is "optional", as explained above
    response = await bot.ask(
        prompt=query,
        conversation_style=ConversationStyle.precise,
        simplify_response=True,
    )
    """
{
    "text": str,
    "author": str,
    "sources": list[dict],
    "sources_text": str,
    "suggestions": list[str],
    "messages_left": int
}
    """
    print(response["messages_left"], "MESSAGES LEFT")
    answer = response["text"]
    await bot.close()
    return answer


def parse(text, source=Sources.OpenAI):
    global query
    modified_query = query % text

    if source == Sources.OpenAI:
        answer = openai(modified_query)
    elif source == Sources.Bing:
        answer = asyncio.run(bing(modified_query))
    else:
        answer = ""

    try:
        start = answer.find("```json\n") + len("```json\n")
        end = answer.find("}\n```") + 1
        json_content = answer[start:end]

        if source == Sources.Bing:
            # total and tax are the two numerical keys where bing may erroneously add an expression
            # we evaluate and replace them before converting to JSON
            TOTAL_REGEX = r'([\s\S]+"total": )([^,}]+)([\s\S]+)'
            TAX_REGEX = r'([\s\S]+"tax": {[^:]+: )(.+)([\s\S]+)'

            for regex in (TOTAL_REGEX, TAX_REGEX):
                expression = re.search(regex, json_content)
                if not expression:
                    if not '"tax": null' in json_content:
                        regex_type = "TOTAL" if regex == TOTAL_REGEX else "TAX"
                        raise json.JSONDecodeError(
                            f"Expression evaluation regex failed for {regex_type}_REGEX",
                            json_content,
                            -1,
                        )
                    else:
                        continue
                expression = expression.group(2)
                try:
                    evaluated = eval(expression)
                except:
                    if expression == "null":
                        evaluated = "null"
                    else:
                        evaluated = f'"{expression}"'
                json_content = re.sub(
                    regex, r"\g<1>" + str(evaluated) + r"\g<3>", json_content
                )

        return json.loads(json_content)
    except json.JSONDecodeError as e:
        print(
            f"{source} was unable to provide a proper response to the following query:"
        )
        print("".join("\t" + line for line in modified_query.splitlines(True)))
        print("Response:")
        print("".join("\t" + line for line in answer.splitlines(True)))
        print("JSON Content:")
        print("".join("\t" + line for line in json_content.splitlines(True)))
        raise e


if __name__ == "__main__":
    text = """amazonin
we)

Sold By :

Spigen India Pvt. Ltd.

* Rect/Killa Nos. 38//8/2 min, 192//22/1,196//2/1/1,     
37//15/1, 15/2,, Adjacent to Starex School, Village      
- Binola, National Highway -8, Tehsil - Manesar
Gurgaon, Haryana, 122413

IN

PAN No: ABACS5056L
GST Registration No: O6ABACS5056L12Z5

Order Number: 407-5335982-7837125
Order Date: 30.05.2023

Tax Invoice/Bill of Supply/Cash Memo
(Original for Recipient)

Billing Address :

Praveen Bohra

E-303, ParkView City 2, Sector 49, Sohna Road
GURGAON, HARYANA, 122018

IN

State/UT Code: 06

Shipping Address :

Praveen Bohra

Praveen Bohra

E-303, ParkView City 2, Sector 49, Sohna Road
GURGAON, HARYANA, 122018

IN

State/UT Code: 06

Place of supply: HARYANA

Place of delivery: HARYANA

Invoice Number : DEL5-21033
Invoice Details : HR-DEL5-918080915-2324
Invoice Date : 30.05.2023

Description at Tax |Tax /|Tax Total
p y Rate |Type |Amount|Amount

Black) | BO8BHLZHBH ( ACS01744INP )
HSN:39269099

1 |Spigen Liquid Air Back Cover Case for iPhone 12 Mini (TPU | Matte
1846.62] 1 |%846.62| 9% |CGST! %76.19 |%999.00
9% |SGST| %76.19

TOTAL:

Amount in Words:
Nine Hundred Ninety-nine only

Whether tax is payable under reverse charge - No

For Spigen India Pvt. Ltd.:
sSoigenrn

Authorized Signatory

Payment Transaction ID: Date & Time: 30/05/2023, 10:48:43 Invoice Value: Mode of Payment: Credit
2rs9ZEF8BwU9VmWiCc2Us hrs 999.00 Card

*ASSPL-Amazon Seller Services Pvt. Ltd., ARIPL-Amazon Retail India Pvt. Ltd. (only where Amazon Retail India Pvt. Ltd. fulfillment center is co-located)

Customers desirous of availing input GST credit are requested to create a Business account and purchase on Amazon.in/business from Business eligible offers

Please note that this invoice is not a demand for payment

Page 1 of 1"""
    print(parse(text, Sources.Bing))
