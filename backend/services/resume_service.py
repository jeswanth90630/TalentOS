from ai.parser import parse_resume, extract_text_from_file_bytes

def process_resume_file(file_bytes: bytes, filename: str):
    """
    Parses uploaded PDF or DOCX file content and returns structured AI extraction data.
    """
    raw_text = extract_text_from_file_bytes(file_bytes, filename)
    return parse_resume(raw_text, filename)
