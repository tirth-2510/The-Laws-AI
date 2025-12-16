from fastapi import HTTPException
import json
from io import BytesIO
import re
import pdfplumber

# <----- MAIN Function ----->
def extractor(file, type: str, category: str):
    match category:
        case "order":
            if type=="pdf":
                return order_extractor(file)
            elif type == "json":
                return judgement_extractor(file)
        
        case "act":
            return act_extractor(file)

        case _:
            raise HTTPException(detail="Unsupported file format!!!", status_code=400)

# <----- ORDER EXTRACTOR ----->
def clean_repeated_noise(text: str) -> str:
    noise_patterns = [
        r"Downloaded on\s*:\s*.*",
        r"\bNEUTRAL\s+CITATION\b",
        r"\bundefined\b",
        r"CR\.MA\/\d+\/\d+\s+\d+\/\d+\s+JUDGMENT",
    ]

    for pattern in noise_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    text = re.sub(r"\n=+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def cleanup_order_text(text: str):
    text = clean_repeated_noise(text)
    date_match = re.search(
        r"(.*?Date\s*:\s*\d{2}/\d{2}/\d{4})",
        text,
        re.DOTALL
    )
    if date_match:
        metadata = date_match.group(1).strip()
        main_content = text[date_match.end():].strip()
    else:
        outcomes = re.split("=.+=", text)
        main_content = outcomes[-1]
        metadata = "\n".join(outcomes[:-1])

    return metadata, main_content

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
def get_judgement_metadata(content:dict):
    Title=content.get("Title")
    Country=content.get("Country",{}).get("Name")
    Court_Name=content.get("Court",{}).get("Name")
    Court_Type=content.get("Court",{}).get("Type")
    Date=content.get("JudgmentDate")
    isoverruled=content.get("IsOverRuled")
    Bench=content.get("Bench")
    judgebench=content.get("JudgeBench")
    references = content.get("References", [])
    reference_text = ""
    if references:
        reference_lines = []
        for ref in references:
            ref_title = ref.get("Title", "")
            ref_citation = ref.get("Citation", "")
            ref_case_type = ref.get("CaseType", "")

            reference_lines.append(
                f"\n\t{ref_title}\n\tCitation: {ref_citation}\n\tCaseType: {ref_case_type}"
            )
        reference_text = "\n".join(reference_lines)
    act_references = content.get("ActReferrences", [])
    act_text = ""
    if act_references:
        act_lines = []
        for act in act_references:
            act_name = act.get("Act", "")
            sections = act.get("Sections", [])

            for sec in sections:
                section = sec.get("Section", "")
                section_title = sec.get("Title", "")

                act_lines.append(
                    f"\n\t{act_name}\n\tSection: {section}\n\tSection Title: {section_title}"
                )

        act_text = "\n".join(act_lines)
    Judges=""
    Advocates=""
    Respondants=""
    Appellants=""
    if(content.get("Appellants",[])):
        appell=content.get("Appellants")
        Appellants=", ".join(appell)  
    else:
        Appellants=""
    if(content.get("Respondants",[])):
        Respond=content.get("Respondants",[])
        Respondants=", ".join(Respond)
    else:
        Respondants=""
    if(content.get("Advocates",[])):
        advocate=content.get("Advocates",[])
        Advocates= ", ".join(advocate)
    else:
        Advocates=""
    if(content.get("Judges",[])):
        Judge=content.get("Judges",[])
        Judges=", ".join(Judge)
    else:
        Judges=""
    deliveringjudge=content.get("DeliveringJudges")
    AppealType=content.get("AppealType")
    FinalVerdict=content.get("FinalVerdict")

    return f"""Title: {Title},
Country: {Country},
Court Name: {Court_Name},
Court Type: {Court_Type},
Judgement Date: {Date},
Is Over Ruled:{isoverruled},
Bench:{Bench},
Judge Bench:{judgebench}\n
References:{reference_text}\n
Act References:{act_text}\n
Appellants: {Appellants},
Respondants: {Respondants},
Advocates: {Advocates},
Judges: {Judges},
Delivering Judge:{deliveringjudge},
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
