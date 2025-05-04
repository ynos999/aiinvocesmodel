## AI Invoces Model
### For Windows:
### python -m venv venv
### .\venv\Scripts\activate
### python.exe -m pip install --upgrade pip
### pip install -r requirements.txt
### python generate_invoices.py
### python 2.learn_model.py
### python 3.invoices_processor.py .\invoices\pdf\invoice_11.pdf
### python 3.invoices_processor.py .\sample-invoice.pdf
### python 4.update_invoices_model.py

#### invoices/
#### ├── dataset/
#### │   └── invoices_metadata.csv
#### ├── pdf/
#### │   ├── invoice_0.pdf
#### │   └── invoice_1.pdf
#### ├── images/
#### │   ├── invoice_0.jpg
#### │   └── invoice_1.png
#### ├── new_dataset/
#### │   └── invoices_metadata.csv
#### ├── newpdf/
#### │   ├── invoice_9910.pdf
#### │   └── invoice_9911.pdf
#### ├── newimages/
#### │   ├── invoice_9910.jpg
#### │   └── invoice_9920.png
#### ├── processed/
####
####
#### invoices_metadata.csv
#### company,invoice_number,date,items,total_amount,currency,language,invoice_text,date_text,total_text,file_path,file_type
#### "РАО «Наумова, Беляков и Щербакова»",INV-8941-414,08.02.2025,"[{'name': 'сбросить', 'quantity': 10, 'price': 438.45, 'total': 4384.5}, {'name': 'протягивать', 'quantity': 9, 'price': 158.27, 'total': 1424.43}, {'name': 'бегать', 'quantity': 6, 'price': 393.91, 'total': 2363.46}, {'name': 'построить', 'quantity': 8, 'price': 891.97, 'total': 7135.76}, {'name': 'домашний', 'quantity': 8, 'price': 181.29, 'total': 1450.32}]",4025.09,₽,ru,Счет-фактура №,Дата:,Итого:,invoices/pdf/invoice_0.pdf,pdf

#### https://github.com/tesseract-ocr/tessdata
#### C:\Program Files\Tesseract-OCR
#### PATH (Windows 10/11)
#### Windows key + R, write sysdm.cpl and push Enter
#### Go to the "Advanced"
#### Click "Environment Variables"
#### "System variables" find "Path" and push "Edit"
#### Clik "New" and past way to Tesseract folder (C:\Program Files\Tesseract-OCR)
#### Clik "OK"
##### tesseract --version

#### https://github.com/oschwartz10612/poppler-windows/releases/
#### C:\Program Files\poppler-24.08.0\Library\bin
#### PATH (Windows 10/11)
#### Windows key + R, write sysdm.cpl and push Enter
#### Go to the "Advanced"
#### Click "Environment Variables"
#### "System variables" find "Path" and push "Edit"
#### Clik "New" and past way to Tesseract folder (C:\Program Files\poppler-24.08.0\Library\bin)
#### Clik "OK"
#### pdftoppm -v

#### Linux (Ubuntu/Debian):
#### sudo apt update
#### sudo apt install tesseract-ocr
#### sudo apt install tesseract-ocr-lav tesseract-ocr-eng tesseract-ocr-rus
#### 
#### MacOS:
#### brew install tesseract
#### brew install tesseract-lang

#### For Ubuntu/Debian:
#### sudo apt update
#### sudo apt install poppler-utils
#### Additional development packages (if needed):
#### sudo apt install libpoppler-cpp-dev
#### pdftoppm -v
#### 
#### For macOS:
#### brew install poppler
#### bbrew install pkg-config  # Required for some Python packages
#### pdftoppm -v
#### 
#### After installing Poppler, modify your Python script to use the correct path.
#### 
#### For Ubuntu (usually in default PATH):
#### poppler_path = None  # Or '/usr/bin' if needed
#### 
#### For macOS with Homebrew:
#### poppler_path = '/opt/homebrew/bin'  # M1/M2 Macs
#### OR
#### poppler_path = '/usr/local/bin'     # Intel Macs
###
####
#### What you need to prepare:
#### 
#### CSV file with columns: company, invoice_number, date, products, total_amount, currency, language, invoice_text, date_text, total_text, file_path, file_type
####
#### The original NER model must be restored in the invoice_ner_model folder
####
#### Poppler and Tesseract must be installed correctly (paths must be configured)