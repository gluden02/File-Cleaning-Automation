# 📚 ReadEra → AnkiDroid Automation

**Personal Project – January 2026**

Python automation project designed to transform vocabulary exported from **ReadEra** into decks compatible with **AnkiDroid**, improving language learning through structured data processing.

---

## 🧠 Project Overview

This project takes vocabulary files exported from ReadEra and automatically processes them to generate **CSV files ready for direct import into AnkiDroid**. The pipeline includes data cleaning, normalization, translation, and enrichment, applying best practices in **data preprocessing**, **automation**, and **API integration**.

The main goal is to **reduce manual effort** and **increase the quality and consistency of study material** for language learning.

---

## ⚙️ Key Features

* Text cleaning and normalization (lowercasing, removal of unwanted characters)
* Duplicate removal and management of repeated terms
* Data processing using **pandas**
* Integration with external APIs for:

  * Automatic **EN → ES translation**
  * English definitions retrieval
* Creation of structured datasets
* Final export to **CSV format**, fully compatible with AnkiDroid

---

## 🛠️ Technologies Used

* Python 3
* pandas
* External translation and dictionary APIs
* Jupyter Notebook

---

## 📥 Input

* Vocabulary file exported from **ReadEra**

## 📤 Output

* **CSV file** ready to be imported into **AnkiDroid** as a study deck

---

## 🚀 How to Use

1. Export vocabulary from ReadEra
2. Run the processing notebook
3. Configure API credentials (if required)
4. Generate the final CSV file
5. Import the CSV into AnkiDroid

---

## 📌 Best Practices Applied

* Automation of repetitive tasks
* Clear separation of processing stages
* Responsible API usage
* Clean and structured data output for downstream consumption

---

## 🔮 Possible Future Improvements

* Support for additional languages
* Output format customization
* Command-line interface (CLI)
* API result caching to reduce external calls

---

## 👤 Author
Emanuel Etcheverry  
Technology Management Student | Python & Data Automation