# ocr_rag.py
import requests

def extract_text_from_pdf(pdf_path: str, api_key: str) -> str:
    """
    Extracts text from a handwritten or scanned PDF using OCR.space API.
    
    Args:
        pdf_path (str): Path to the local PDF file.
        api_key (str): Your OCR.space API key.
    
    Returns:
        str: Extracted text from the PDF.
    """
    with open(pdf_path, 'rb') as f:
        files = {'file': f}
        payload = {
            'language': 'eng',
            'isOverlayRequired': False,
            'filetype': 'PDF',
            'detectOrientation': True,
            'isCreateSearchablePdf': False,
            'isSearchablePdfHideTextLayer': False,
            'scale': True,
            'isTable': False,
            'OCREngine': 2
        }
        headers = {'apikey': api_key}

        response = requests.post(
            'https://api.ocr.space/parse/image',
            files=files,
            data=payload,
            headers=headers
        )

    result = response.json()
    if result.get('IsErroredOnProcessing'):
        raise Exception(f"OCR Error: {result.get('ErrorMessage', 'Unknown error')}")

    return result['ParsedResults'][0]['ParsedText']
