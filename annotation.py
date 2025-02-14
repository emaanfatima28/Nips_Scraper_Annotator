import os
import fitz  
import mysql.connector
import google.generativeai as genai
from tqdm import tqdm
import google.api_core.exceptions
import time

# Configure API
genai.configure(api_key="your_api_key")
model = genai.GenerativeModel("gemini-pro")

# Connect to database
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="research_papers"
)
cursor = db.cursor()

def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = "".join([page.get_text("text") for page in doc])
        return text.strip()
    except fitz.EmptyFileError:
        print(f"Skipping empty or corrupted file: {pdf_path}")
        return None

def classify_paper(title, abstract):
    prompt = f"""Classify the following research paper into one of these categories:
    - Deep Learning
    - Computer Vision
    - Reinforcement Learning
    - NLP
    - Optimization

    Title: {title}
    Abstract: {abstract}

    Respond with only the category name."""
    valid_categories = {"Deep Learning", "Computer Vision", "Reinforcement Learning", "NLP", "Optimization"}
    
    retries = 3
    for attempt in range(retries):
        try:
            response = model.generate_content(prompt)
            category = response.text.strip()
            if category in valid_categories:
                return category
            return None  # Skip if category is not valid
        except google.api_core.exceptions.ResourceExhausted:
            wait_time = (attempt + 1) * 10  # Exponential backoff
            print(f"Quota exceeded. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        except Exception as e:
            print(f"Error classifying paper: {e}")
            return None
    return None

def process_pdf(file_path):
    title = os.path.basename(file_path).replace(".pdf", "")
    abstract = extract_text_from_pdf(file_path)
    if abstract is None:
        return  # Skip processing if the file is empty or corrupted
    
    abstract = abstract[:1000]  
    category = classify_paper(title, abstract)
    if category:
        sql = "INSERT INTO papers (title, category) VALUES (%s, %s)"
        cursor.execute(sql, (title, category))
        db.commit()
        print(f"Inserted: {title} -> {category}")
    else:
        print(f"Skipped: {title} (No valid category)")

pdf_folder = "path_where_files_are_placed"
files = [f for f in os.listdir(pdf_folder) if f.endswith(".pdf")]

for file_name in tqdm(files, desc="Processing PDFs"):
    process_pdf(os.path.join(pdf_folder, file_name))

cursor.close()
db.close()
