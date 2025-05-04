import os
import pandas as pd
import pytesseract
from pdf2image import convert_from_path
import spacy
from spacy.training.example import Example
from sklearn.model_selection import train_test_split
from tqdm import tqdm
import cv2
import numpy as np
import random
from PIL import Image

# =============================================
# KONFIGURĀCIJA - LABOT ATBILSTOŠI SAVAI SISTĒMAI
# =============================================

# Norādiet pilno ceļu uz Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Norādiet pilno ceļu uz Poppler
poppler_path = r"C:\Program Files\poppler-24.08.0\Library\bin"

# OCR valodu konfigurācija
tesseract_langs = 'lav+eng+rus'

# =============================================
# PALĪGFUNKCIJAS
# =============================================

def preprocess_image(image):
    """Attēlu priekšapstrāde OCR uzlabošanai"""
    # Konvertēšana uz pelēko toņu
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Adaptīvs slieksnis
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    
    # Trokšņu mazināšana
    denoised = cv2.fastNlMeansDenoising(thresh, h=10)
    
    return denoised

def extract_text_from_file(file_path, file_type):
    """Iegūst tekstu no PDF, JPG vai PNG faila"""
    try:
        if file_type.lower() == 'pdf':
            # PDF apstrāde ar Poppler
            images = convert_from_path(file_path, poppler_path=poppler_path)
            full_text = ""
            
            for img in images:
                img_np = np.array(img)
                # Konvertē no RGB uz BGR (OpenCV formāts)
                img_np = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
                processed_img = preprocess_image(img_np)
                text = pytesseract.image_to_string(processed_img, lang=tesseract_langs)
                full_text += text + "\n"
            
            return full_text.strip()
        
        else:  # Attēlu formāti (JPG/PNG)
            img = cv2.imread(file_path)
            if img is None:
                raise ValueError(f"Neizdevās nolasīt attēlu no {file_path}")
                
            processed_img = preprocess_image(img)
            text = pytesseract.image_to_string(processed_img, lang=tesseract_langs)
            return text.strip()
            
    except Exception as e:
        print(f"Kļūda apstrādājot {file_path}: {str(e)}")
        return ""

# =============================================
# GALVENĀ APSTRĀDES FUNKCIJA
# =============================================

def prepare_training_data(metadata_path):
    """Sagatavo apmācības datus no metadatu faila"""
    # Ielādējam metadatus
    df = pd.read_csv(metadata_path)
    
    # Inicializējam Spacy modeli
    nlp = spacy.blank("xx")  # Daudzvalodu modelis
    
    # Pievienojam NER pipeli
    if "ner" not in nlp.pipe_names:
        ner = nlp.add_pipe("ner")
    else:
        ner = nlp.get_pipe("ner")
    
    # Pievienojam entītiju kategorijas
    for label in ["COMPANY", "INVOICE_NUMBER", "DATE", "AMOUNT", "CURRENCY"]:
        ner.add_label(label)
    
    # Sagatavojam apmācības datus
    TRAIN_DATA = []
    skipped_files = 0
    
    print("\nSākam datu sagatavošanu...")
    for idx, row in tqdm(df.iterrows(), total=len(df)):
        try:
            text = extract_text_from_file(row['file_path'], row['file_type'])
            
            if not text:
                skipped_files += 1
                continue
                
            entities = []
            
            # Uzņēmuma nosaukums
            company_start = text.find(row['company'])
            if company_start != -1:
                entities.append((company_start, company_start + len(row['company']), "COMPANY"))
            
            # Pavadzīmes numurs
            inv_start = text.find(row['invoice_number'])
            if inv_start != -1:
                entities.append((inv_start, inv_start + len(row['invoice_number']), "INVOICE_NUMBER"))
            
            # Datums
            date_start = text.find(row['date'])
            if date_start != -1:
                entities.append((date_start, date_start + len(row['date']), "DATE"))
            
            # Summa un valūta
            amount_str = f"{row['total_amount']:.2f}"
            amount_start = text.find(amount_str)
            if amount_start != -1:
                entities.append((amount_start, amount_start + len(amount_str), "AMOUNT"))
                
                # Valūta
                currency_start = text.find(row['currency'], amount_start)
                if currency_start != -1:
                    entities.append((currency_start, currency_start + len(row['currency']), "CURRENCY"))
            
            if entities:
                TRAIN_DATA.append((text, {"entities": entities}))
                
        except Exception as e:
            print(f"\nKļūda apstrādājot {row['file_path']}: {str(e)}")
            skipped_files += 1
    
    print(f"\nDatu sagatavošana pabeigta. Izlaistie faili: {skipped_files}/{len(df)}")
    return nlp, TRAIN_DATA

# =============================================
# MODEĻA APMĀCĪBA
# =============================================

def train_model(nlp, train_data, test_size=0.2, epochs=20):
    """Apmāca NER modeli"""
    # Sadalām datus apmācībai un testēšanai
    train_data, test_data = train_test_split(train_data, test_size=test_size, random_state=42)
    
    print("\nSākam modeļa apmācību...")
    optimizer = nlp.begin_training()
    
    # Epohu skaits
    for epoch in range(epochs):
        random.shuffle(train_data)
        losses = {}
        
        # Batch apstrāde
        batch_size = 8
        batches = [train_data[i:i + batch_size] for i in range(0, len(train_data), batch_size)]
        
        for batch in tqdm(batches, desc=f"Epoha {epoch + 1}/{epochs}"):
            examples = []
            for text, annotations in batch:
                doc = nlp.make_doc(text)
                example = Example.from_dict(doc, annotations)
                examples.append(example)
            
            nlp.update(examples, drop=0.3, losses=losses, sgd=optimizer)
        
        print(f"Epoha {epoch + 1}, Zaudējumi: {losses}")
    
    # Testējam modeli
    print("\nTestējam modeli...")
    correct = 0
    total = 0
    
    for text, annotations in tqdm(test_data, desc="Testēšana"):
        doc = nlp(text)
        true_entities = set((start, end, label) for start, end, label in annotations["entities"])
        pred_entities = set((ent.start_char, ent.end_char, ent.label_) for ent in doc.ents)
        
        correct += len(true_entities & pred_entities)
        total += len(true_entities)
    
    accuracy = correct / total if total > 0 else 0
    print(f"\nPrecizitāte: {accuracy:.2%}")
    
    return nlp

# =============================================
# GALVENĀ IZPILDES DAĻA
# =============================================

if __name__ == "__main__":
    # 1. Sagatavojam datus
    nlp, train_data = prepare_training_data("invoices/dataset/invoices_metadata.csv")
    
    # 2. Apmācam modeli
    trained_nlp = train_model(nlp, train_data)
    
    # 3. Saglabājam modeli
    trained_nlp.to_disk("invoice_ner_model")
    print("\nModelis veiksmīgi saglabāts mapē 'invoice_ner_model'")