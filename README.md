# 📚 ReadEra → AnkiDroid Automation

Personal Project – January 2026

Python automation project designed to transform vocabulary exported from ReadEra into decks compatible with AnkiDroid, improving language learning through structured data processing.

## 🧠 Project Overview

This project takes vocabulary files exported from ReadEra and automatically processes them into structured CSV files ready for direct import into AnkiDroid.

The pipeline includes:

* data cleaning and normalization
* duplicate handling
* automatic translation (EN → ES)
* dictionary-based definition lookup
* structured export to CSV

The main goal is to reduce manual effort and improve the quality and consistency of study material for language learning.

## ⚙️ Key Features

* Text cleaning and normalization
* Removal and annotation of duplicate terms
* Data processing with `pandas`
* External API integration for:

  * automatic EN → ES translation
  * English definition retrieval
* Streamlit web app for easy use
* CSV export fully compatible with AnkiDroid

## 🛠️ Technologies Used

* Python 3
* Streamlit
* pandas
* requests
* deep-translator
* External translation and dictionary APIs

## 📦 Project Structure

* `app.py` → Streamlit interface
* `clean_automation.py` → cleaning, enrichment, and export logic
* `requirements.txt` → dependencies
* `input/` → optional folder for local CLI input files
* `output/` → optional folder for CLI exports

## 📥 Input

A vocabulary file exported from ReadEra in pipe-delimited format (`.txt` or `.csv`).

## 📤 Output

A CSV file ready to be imported into AnkiDroid as a study deck.

## 🚀 How to Run

### Option 1: Web App (recommended)

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the app:

```bash
streamlit run app.py
```

Then:

1. Upload the ReadEra export file.
2. Enter the book name and output filename.
3. Click **Process**.
4. Download the generated CSV file.

### Option 2: Command-Line Interface (CLI)

The processing logic can also be executed from the terminal using:

```bash
python clean_automation.py
```

This mode uses interactive prompts to select:

* input file
* output directory
* output filename
* book name

## 📌 Best Practices Applied

* Automation of repetitive tasks
* Clear separation between interface and processing logic
* Responsible API usage
* Clean and structured output for downstream consumption

## 🔮 Possible Future Improvements

* Support for additional languages
* Output format customization
* Command-line arguments instead of prompts
* API result caching to reduce external calls
* Progress history and processing logs

## 👤 Author

Emanuel Etcheverry
Technology Management Student | Python & Data Automation
