import os
import pandas as pd
import pytesseract
from pdf2image import convert_from_path
import spacy
from spacy.training.example import Example
from tqdm import tqdm
import cv2
import numpy as np
import random
import shutil

# =============================================
# KONFIGURĀCIJA
# =============================================
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
poppler_path = r"C:\Program Files\poppler-24.08.0\Library\bin"
tesseract_langs = 'lav+eng+rus'

PDF_DIR = "invoices/newpdf"       # ← mainīts
IMG_DIR = "invoices/newimages"
PROCESSED_DIR = "invoices/processed"
CSV_PATH = "invoices/new_dataset/invoices_metadata.csv"

os.makedirs(PROCESSED_DIR, exist_ok=True)

# =============================================
# FUNKCIJAS
# =============================================

def preprocess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    denoised = cv2.fastNlMeansDenoising(thresh, h=10)
    return denoised

def extract_text_from_file(file_path, file_type):
    try:
        if file_type.lower() == 'pdf':
            images = convert_from_path(file_path, poppler_path=poppler_path)
            full_text = ""
            for img in images:
                img_np = np.array(img)
                img_np = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
                processed_img = preprocess_image(img_np)
                text = pytesseract.image_to_string(processed_img, lang=tesseract_langs)
                full_text += text + "\n"
            return full_text.strip()
        else:
            img = cv2.imread(file_path)
            if img is None:
                raise ValueError(f"Neizdevās nolasīt attēlu no {file_path}")
            processed_img = preprocess_image(img)
            text = pytesseract.image_to_string(processed_img, lang=tesseract_langs)
            return text.strip()
    except Exception as e:
        print(f"Kļūda apstrādājot {file_path}: {str(e)}")
        return ""

def get_full_file_path(file_name, file_type):
    ext = file_type.lower()
    if ext == "pdf":
        return os.path.join(PDF_DIR, file_name)  # ← mainīts
    elif ext in ["jpg", "jpeg", "png"]:
        return os.path.join(IMG_DIR, file_name)
    else:
        return None

def update_model_with_new_invoices(metadata_df):
    print("\nIelādējam esošo modeli...")
    nlp = spacy.load("invoice_ner_model")

    if "ner" not in nlp.pipe_names:
        ner = nlp.add_pipe("ner")
    else:
        ner = nlp.get_pipe("ner")

    for label in ["COMPANY", "INVOICE_NUMBER", "DATE", "AMOUNT", "CURRENCY"]:
        if label not in ner.labels:
            ner.add_label(label)

    TRAIN_DATA = []
    skipped = 0

    print("Apstrādājam jaunās pavadzīmes un attēlus...")
    for _, row in tqdm(metadata_df.iterrows(), total=len(metadata_df)):
        try:
            file_path = get_full_file_path(row['file_path'], row['file_type'])
            if not file_path or not os.path.exists(file_path):
                print(f"Failu nevar atrast: {file_path}")
                skipped += 1
                continue

            text = extract_text_from_file(file_path, row['file_type'])

            if not text:
                skipped += 1
                continue

            entities = []
            company_start = text.find(row['company'])
            if company_start != -1:
                entities.append((company_start, company_start + len(row['company']), "COMPANY"))

            inv_start = text.find(row['invoice_number'])
            if inv_start != -1:
                entities.append((inv_start, inv_start + len(row['invoice_number']), "INVOICE_NUMBER"))

            date_start = text.find(row['date'])
            if date_start != -1:
                entities.append((date_start, date_start + len(row['date']), "DATE"))

            amount_str = f"{row['total_amount']:.2f}"
            amount_start = text.find(amount_str)
            if amount_start != -1:
                entities.append((amount_start, amount_start + len(amount_str), "AMOUNT"))

                currency_start = text.find(row['currency'], amount_start)
                if currency_start != -1:
                    entities.append((currency_start, currency_start + len(row['currency']), "CURRENCY"))

            if entities:
                TRAIN_DATA.append((text, {"entities": entities}))
                dest_path = os.path.join(PROCESSED_DIR, row['file_path'])
                shutil.move(file_path, dest_path)
                metadata_df = metadata_df.drop(index=_)
            else:
                skipped += 1

        except Exception as e:
            print(f"Kļūda apstrādājot {row['file_path']}: {str(e)}")
            skipped += 1

    if not TRAIN_DATA:
        print("❌ Nav derīgu datu. Treniņš netiks veikts.")
        return

    print(f"\nSākam modeļa papildināšanu ar {len(TRAIN_DATA)} piemēriem...")
    optimizer = nlp.resume_training()
    for epoch in range(5):
        random.shuffle(TRAIN_DATA)
        losses = {}
        examples = [Example.from_dict(nlp.make_doc(text), ann) for text, ann in TRAIN_DATA]
        nlp.update(examples, drop=0.3, losses=losses, sgd=optimizer)
        print(f"Epoha {epoch + 1}, zaudējumi: {losses}")

    print("\nSaglabājam atjaunināto modeli...")
    nlp.to_disk("invoice_ner_model")
    print(f"✅ Modelis veiksmīgi atjaunināts un saglabāts. Izlaistie faili: {skipped}/{len(metadata_df)}")

    # Saglabājam atjaunināto CSV
    metadata_df.to_csv(CSV_PATH, index=False)
    print(f"✅ CSV fails veiksmīgi atjaunināts.")

# =============================================
# GALVENĀ IZPILDE
# =============================================

if __name__ == "__main__":
    df = pd.read_csv(CSV_PATH)
    update_model_with_new_invoices(df)
