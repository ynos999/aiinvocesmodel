import os
import random
from faker import Faker
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import pandas as pd
from tqdm import tqdm

# Reģistrējam Unicode fontu PDF ģenerēšanai
pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))

# Izveidojam mapes struktūru
os.makedirs("invoices/pdf", exist_ok=True)
os.makedirs("invoices/images", exist_ok=True)
os.makedirs("invoices/dataset", exist_ok=True)

# Inicializējam Faker dažādām valodām
fake_lv = Faker('lv_LV')
fake_en = Faker('en_US')
fake_ru = Faker('ru_RU')

def generate_invoice_data(language):
    """Ģenerē pavadzīmes datus noteiktā valodā"""
    if language == 'lv':
        fake = fake_lv
        invoice_text = "Pavadzīme Nr."
        date_text = "Datums:"
        total_text = "Kopsumma:"
        currency = random.choice(["EUR", "€"])
    elif language == 'en':
        fake = fake_en
        invoice_text = "Invoice No."
        date_text = "Date:"
        total_text = "Total:"
        currency = random.choice(["USD", "$"])
    elif language == 'ru':
        fake = fake_ru
        invoice_text = "Счет-фактура №"
        date_text = "Дата:"
        total_text = "Итого:"
        currency = random.choice(["RUB", "₽"])
    
    company = fake.company()
    invoice_number = f"INV-{random.randint(1000, 9999)}-{random.randint(100, 999)}"
    date = (datetime.now() - timedelta(days=random.randint(0, 365))).strftime("%d.%m.%Y")
    amount = round(random.uniform(10, 10000), 2)
    
    items = []
    for _ in range(random.randint(1, 10)):
        item_name = fake.word()
        quantity = random.randint(1, 10)
        price = round(random.uniform(1, 1000), 2)
        items.append({
            'name': item_name,
            'quantity': quantity,
            'price': price,
            'total': quantity * price
        })
    
    return {
        'company': company,
        'invoice_number': invoice_number,
        'date': date,
        'items': items,
        'total_amount': amount,
        'currency': currency,
        'language': language,
        'invoice_text': invoice_text,
        'date_text': date_text,
        'total_text': total_text
    }

def create_pdf_invoice(data, filename):
    """Izveido PDF pavadzīmi"""
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    c.setFont("DejaVuSans", 16)
    c.drawString(50, height - 50, data['company'])

    c.setFont("DejaVuSans", 12)
    c.drawString(50, height - 100, f"{data['invoice_text']} {data['invoice_number']}")
    c.drawString(50, height - 120, f"{data['date_text']} {data['date']}")

    c.drawString(50, height - 160, "Prece:")
    c.drawString(200, height - 160, "Daudzums:")
    c.drawString(300, height - 160, "Cena:")
    c.drawString(400, height - 160, "Summa:")

    y_position = height - 180
    for item in data['items']:
        c.drawString(50, y_position, item['name'])
        c.drawString(200, y_position, str(item['quantity']))
        c.drawString(300, y_position, f"{item['price']:.2f}")
        c.drawString(400, y_position, f"{item['total']:.2f}")
        y_position -= 20

    c.setFont("DejaVuSans", 14)
    c.drawString(300, y_position - 40, f"{data['total_text']}: {data['total_amount']:.2f} {data['currency']}")

    c.save()

def create_image_invoice(data, filename, img_format='JPEG'):
    """Izveido attēla formāta pavadzīmi (JPG/PNG)"""
    img = Image.new('RGB', (800, 1200), color=(255, 255, 255))
    d = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 20)
    except:
        font = ImageFont.load_default()

    d.text((50, 50), data['company'], fill=(0, 0, 0), font=font)
    d.text((50, 100), f"{data['invoice_text']} {data['invoice_number']}", fill=(0, 0, 0), font=font)
    d.text((50, 130), f"{data['date_text']} {data['date']}", fill=(0, 0, 0), font=font)

    d.text((50, 200), "Prece:", fill=(0, 0, 0), font=font)
    d.text((200, 200), "Daudzums:", fill=(0, 0, 0), font=font)
    d.text((300, 200), "Cena:", fill=(0, 0, 0), font=font)
    d.text((400, 200), "Summa:", fill=(0, 0, 0), font=font)

    y_position = 230
    for item in data['items']:
        d.text((50, y_position), item['name'], fill=(0, 0, 0), font=font)
        d.text((200, y_position), str(item['quantity']), fill=(0, 0, 0), font=font)
        d.text((300, y_position), f"{item['price']:.2f}", fill=(0, 0, 0), font=font)
        d.text((400, y_position), f"{item['total']:.2f}", fill=(0, 0, 0), font=font)
        y_position += 30

    d.text((300, y_position + 40), f"{data['total_text']}: {data['total_amount']:.2f} {data['currency']}", 
           fill=(0, 0, 0), font=font)

    img.save(filename, img_format)

# Ģenerējam 200 pavadzīmes katram formātam
dataset = []

print("Ģenerē PDF pavadzīmes...")
for i in tqdm(range(200)):
    lang = random.choice(['lv', 'en', 'ru'])
    data = generate_invoice_data(lang)
    pdf_path = f"invoices/pdf/invoice_{i}.pdf"
    create_pdf_invoice(data, pdf_path)
    data['file_path'] = pdf_path
    data['file_type'] = 'pdf'
    dataset.append(data)

print("Ģenerē JPG pavadzīmes...")
for i in tqdm(range(200)):
    lang = random.choice(['lv', 'en', 'ru'])
    data = generate_invoice_data(lang)
    jpg_path = f"invoices/images/invoice_{i}.jpg"
    create_image_invoice(data, jpg_path, 'JPEG')
    data['file_path'] = jpg_path
    data['file_type'] = 'jpg'
    dataset.append(data)

print("Ģenerē PNG pavadzīmes...")
for i in tqdm(range(200)):
    lang = random.choice(['lv', 'en', 'ru'])
    data = generate_invoice_data(lang)
    png_path = f"invoices/images/invoice_{200+i}.png"
    create_image_invoice(data, png_path, 'PNG')
    data['file_path'] = png_path
    data['file_type'] = 'png'
    dataset.append(data)

df = pd.DataFrame(dataset)
df.to_csv("invoices/dataset/invoices_metadata.csv", index=False)
print("Visas pavadzīmes veiksmīgi ģenerētas un saglabātas!")
