import pytesseract
from pdf2image import convert_from_path
import spacy
import cv2
import numpy as np
import os
from PIL import Image

# =============================================
# KONFIGURĀCIJA (LABOJAM ATBILSTOŠI SAVAI SISTĒMAI)
# =============================================

# Ceļi uz nepieciešamajiem komponentiem
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
POPPLER_PATH = r'C:\Program Files\poppler-24.08.0\Library\bin'
MODEL_PATH = 'invoice_ner_model'  # Mapē, kur saglabāts apmācītais modelis

# OCR valodu konfigurācija
OCR_LANGUAGES = 'lav+eng+rus'

# =============================================
# PALĪGFUNKCIJAS
# =============================================

def setup_environment():
    """Inicializē vides mainīgos un pārbauda atkarības"""
    # Konfigurē Tesseract ceļu
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
    
    # Pārbauda, vai modelis eksistē
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Nevar atrast modeli mapē '{MODEL_PATH}'")
    
    # Ielādē Spacy modeli
    try:
        nlp = spacy.load(MODEL_PATH)
    except Exception as e:
        raise RuntimeError(f"Nevar ielādēt modeli: {str(e)}")
    
    return nlp

def preprocess_image(image):
    """Attēlu priekšapstrāde OCR uzlabošanai"""
    # Konvertē uz pelēko toņu
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Adaptīvs slieksnis
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    
    # Trokšņu mazināšana
    denoised = cv2.fastNlMeansDenoising(thresh, h=10)
    
    return denoised

def extract_text_from_file(file_path):
    """Iegūst tekstu no PDF, JPG vai PNG faila"""
    try:
        # Noteikt faila tipu
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            # PDF apstrāde
            images = convert_from_path(file_path, poppler_path=POPPLER_PATH)
            full_text = ""
            
            for img in images:
                img_np = np.array(img)
                img_np = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
                processed_img = preprocess_image(img_np)
                text = pytesseract.image_to_string(processed_img, lang=OCR_LANGUAGES)
                full_text += text + "\n"
            
            return full_text.strip()
        
        elif file_ext in ('.jpg', '.jpeg', '.png'):
            # Attēlu apstrāde
            img = cv2.imread(file_path)
            if img is None:
                raise ValueError(f"Nevar nolasīt attēlu no {file_path}")
                
            processed_img = preprocess_image(img)
            return pytesseract.image_to_string(processed_img, lang=OCR_LANGUAGES).strip()
        
        else:
            raise ValueError(f"Nepareizs faila formāts: {file_ext}")
            
    except Exception as e:
        raise RuntimeError(f"Kļūda apstrādājot {file_path}: {str(e)}")

def process_invoice(nlp, file_path):
    """Apstrādā pavadzīmi un atgriež strukturētus datus"""
    try:
        # Iegūst tekstu no faila
        text = extract_text_from_file(file_path)
        
        if not text:
            return {"error": "Neizdevās iegūt tekstu no dokumenta"}
        
        # Apstrādā ar NER modeli
        doc = nlp(text)
        
        # Sagatavo rezultātu struktūru
        result = {
            "company": None,
            "invoice_number": None,
            "date": None,
            "amount": None,
            "currency": None,
            "raw_text": text[:500] + "..." if len(text) > 500 else text,  # Pirmie 500 simboli
            "entities": []
        }
        
        # Iegūst visas atpazītās entītijas
        for ent in doc.ents:
            result["entities"].append({
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char
            })
            
            # Aizpilda galvenos laukus atbilstoši entītiju tipiem
            if ent.label_ == "COMPANY" and not result["company"]:
                result["company"] = ent.text
            elif ent.label_ == "INVOICE_NUMBER" and not result["invoice_number"]:
                result["invoice_number"] = ent.text
            elif ent.label_ == "DATE" and not result["date"]:
                result["date"] = ent.text
            elif ent.label_ == "AMOUNT" and not result["amount"]:
                result["amount"] = ent.text
            elif ent.label_ == "CURRENCY" and not result["currency"]:
                result["currency"] = ent.text
        
        return result
    
    except Exception as e:
        return {"error": str(e)}

# =============================================
# GALVENĀ INTERFEISA FUNKCIJA
# =============================================

def analyze_invoice(file_path):
    """
    Galvenā funkcija pavadzīmju apstrādei
    Atgriež: vārdnīcu ar rezultātiem vai kļūdu
    """
    try:
        # Inicializē vidi un ielādē modeli
        nlp = setup_environment()
        
        # Pārbauda, vai fails eksistē
        if not os.path.exists(file_path):
            return {"error": f"Fails '{file_path}' neeksistē"}
        
        # Apstrādā pavadzīmi
        return process_invoice(nlp, file_path)
    
    except Exception as e:
        return {"error": f"Sistēmas kļūda: {str(e)}"}

# =============================================
# LIETOŠANAS PIEMĒRS
# =============================================

if __name__ == "__main__":
    import argparse
    
    # Argumentu parsēšana
    parser = argparse.ArgumentParser(description='Pavadzīmju apstrādes tools')
    parser.add_argument('file', help='Ceļš uz pavadzīmes failu (PDF, JPG vai PNG)')
    args = parser.parse_args()
    
    # Apstrādā pavadzīmi
    result = analyze_invoice(args.file)
    
    # Rāda rezultātus
    if "error" in result:
        print(f"\nKĻŪDA: {result['error']}")
    else:
        print("\n===== ATPAZĪTIE DATI =====")
        print(f"Uzņēmums: {result['company']}")
        print(f"Pavadzīmes nr.: {result['invoice_number']}")
        print(f"Datums: {result['date']}")
        print(f"Summa: {result['amount']} {result['currency']}")
        
        print("\n===== VISAS ATPAZĪTĀS ENTĪTIJAS =====")
        for ent in result["entities"]:
            print(f"{ent['label']}: {ent['text']} (pozīcija: {ent['start']}-{ent['end']})")
        
        print("\n===== TEKSTS =====")
        print(result["raw_text"])