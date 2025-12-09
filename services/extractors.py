from fastapi import HTTPException
import json
from io import BytesIO
import re
import pdfplumber

# <----- MAIN Function ----->
def extractor(file, type: str, category: str):
    match category:
        case "judgement":
            if type=="pdf":
                return pdf_to_json(file)
            else:
                return judgement_extractor(file)
        
        case "order":
            return order_extractor(file)
        
        case "act":
            return act_extractor(file)

        case _:
            raise HTTPException(detail="Unsupported file format!!!", status_code=400)

# <----- ORDER EXTRACTOR ----->
def cleanup_order_text(text: str):
    outcomes = re.split("=.+=", text)
    # Main Content
    main_content = outcomes[-1]
    metadatas = "\n".join(outcomes[:-1])
    pos=metadatas.find("undefined")
    metadatas= metadatas[pos +len("undefined")+1:]
    return metadatas,main_content

def order_extractor(file):
    file_bytes = file.file.read()
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() or ""
    cleaned_text = cleanup_order_text(text)
    max_chunk_size=2000
    sentences = re.split(r'(?<=[.!?]) +', cleaned_text[1]) 
    chunks = []
    temp_text = ""
    chunks.append(cleaned_text[0])

    for sentence in sentences:
        if len(temp_text) + len(sentence) > max_chunk_size:
            if temp_text:  
                chunks.append(temp_text.strip())
            temp_text = sentence 
        else:
            temp_text += " " + sentence if temp_text else sentence

    if temp_text:
        chunks.append(temp_text.strip())

    return chunks

# <----- JUDGEMENT EXTRACTOR ----->
def pdf_to_json(file):
    file_bytes = file.file.read()
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
    txt=text.replace("\n"," ")
    data=json.loads(txt)
    max_chunk_size = 2000
    output = []
    temp_text = ""
    metadata=get_judgement_metadata(data)
    output.append(metadata)
    data = data.get("JudgementText", {}).get("Paragraphs", [])

    for para in data:
        subparagraphs = para.get("SubParagraphs", [])
        for i, sub in enumerate(subparagraphs):
            text = sub.get("Text", "")
            # add indentation for subpoints
            if sub.get("IsSub"):
                text = "\t" + text

            if len(temp_text) + len(text) > max_chunk_size:
                if temp_text:
                    output.append(temp_text.strip())
                temp_text = text
            else:
                temp_text += text

    # flush leftover text
    if temp_text:
        output.append(temp_text.strip())

    return output


def get_judgement_metadata(content:dict):
     Title=content.get("Title")
     Country=content.get("Country",{}).get("Name")
     Court_Name=content.get("Court",{}).get("Name")
     Court_Type=content.get("Court",{}).get("Type")
     Date=content.get("JudgmentDate")
     if(content.get("Appellants",[])):
        Appellants=content.get("Appellants",[])[0]
     else:
         Appellants=""
     if(content.get("Respondants",[])):
        Respondants=content.get("Respondants",[])[0]
     else:
         Respondants=""
     if(content.get("Advocates",[])):
        Advocates=content.get("Advocates",[])[0]
     else:
         Advocates=""
     if(content.get("Judges",[])):
        Judges=content.get("Judges",[])[0]
     else:
         Judges=""
     AppealType=content.get("AppealType")
     FinalVerdict=content.get("FinalVerdict")

     return f"""Title: {Title},
     Country: {Country},
     Court Name: {Court_Name},
     Court Type: {Court_Type},
     Judgement Date: {Date},
     Appellants: {Appellants},
     Respondants: {Respondants},
     Advocates: {Advocates},
     Judges: {Judges},
     AppealType: {AppealType},
     Final Verdict: {FinalVerdict}"""

def judgement_extractor(file):
    file_bytes = file.file.read()
    content = json.loads(file_bytes)

    max_chunk_size = 2000
    output = []
    temp_text = ""
    metadata=get_judgement_metadata(content)
    output.append(metadata)
    data = content.get("JudgementText", {}).get("Paragraphs", [])

    for para in data:
        subparagraphs = para.get("SubParagraphs", [])
        for i, sub in enumerate(subparagraphs):
            text = sub.get("Text", "")
            # add indentation for subpoints
            if sub.get("IsSub"):
                text = "\t" + text

            if len(temp_text) + len(text) > max_chunk_size:
                if temp_text:
                    output.append(temp_text.strip())
                temp_text = text
            else:
                temp_text += text

    # flush leftover text
    if temp_text:
        output.append(temp_text.strip())

    return output


# <----- ACT EXTRACTOR ----->
def cleanup_act_text(text: str):
    text = re.sub("<Section>", "", text)
    text = re.sub("</Section>", "", text)
    text = re.sub("<SubSection>", "\n\t", text, count=100)
    text = re.sub("</SubSection>", "", text, count=100)
    text = re.sub("<FNR>", "", text, count=100)
    text = re.sub("</FNR>", "", text, count=100)
    text = re.sub("<FN>", "", text, count=100)
    text = re.sub("</FN>", "", text, count=100)
    text = re.sub("<FT>", "", text, count=100)
    text = re.sub("</FT>", "", text, count=100)

    return text

def act_extractor(file):
    file_bytes=file.file
    data = json.load(file_bytes)
    # Main Content.
    text = data.get("text", "No content")
    splitted_text = cleanup_act_text(text)
    max_chunk_size=2000
    sentences = re.split(r'(?<=[.!?]) +', splitted_text) 
    chunks = []
    temp_text = ""

    for sentence in sentences:
        if len(temp_text) + len(sentence) > max_chunk_size:
            if temp_text:  
                chunks.append(temp_text.strip())
            temp_text = sentence 
        else:
            temp_text += " " + sentence if temp_text else sentence

    if temp_text:
        chunks.append(temp_text.strip())

    return chunks
