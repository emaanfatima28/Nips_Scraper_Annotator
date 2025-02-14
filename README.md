# Nips_Scraper

## Install the required dependencies:
```
pip install aiohttp aiofiles beautifulsoup4 lxml pymupdf mysql-connector-python google-generativeai tqdm
```

### Run the script:
```
python script_name.py
```

Ensure you have set up your MySQL database and configured your Google Gemini API key before running the annotation script.

### MySQL Table Creation Query:
```sql
CREATE DATABASE IF NOT EXISTS research_papers;
USE research_papers;

CREATE TABLE IF NOT EXISTS papers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    category VARCHAR(255) NOT NULL
);
```

### Library Usage:
- **aiohttp, aiofiles**: Used for asynchronous web scraping.
- **beautifulsoup4, lxml**: Used for parsing HTML content.
- **pymupdf**: Extracts text from PDF files.
- **mysql-connector-python**: Connects to MySQL database (XAMPP).
- **google-generativeai**: Uses Google Gemini API for paper classification.
- **tqdm**: Displays progress bars for processing.
