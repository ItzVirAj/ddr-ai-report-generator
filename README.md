# DDR AI Report Generator

AI-powered system that converts **building inspection reports and thermal scan reports (PDF)** into a **structured Detailed Diagnostic Report (DDR)** with observations, root causes, severity assessment, and recommended actions.

The system extracts text and images from reports, analyzes the data using **Google Gemini AI**, and generates a **professional HTML diagnostic report**.

---

# Project Overview

Property inspection companies often produce two separate documents:

• **Inspection report** (visual inspection findings)
• **Thermal scan report** (infrared moisture detection)

Manually combining them into a final diagnostic report takes time and expertise.

This project automates that process using **AI + document extraction + rule-based scoring**.

The system:

1. Extracts **text and images** from PDFs
2. Identifies **dampness, seepage, structural cracks, and plumbing issues**
3. Combines **inspection + thermal data**
4. Generates a **structured DDR report**
5. Produces a **professional HTML report with images**

---

# Features

## PDF Data Extraction

* Extracts **text from inspection reports**
* Extracts **thermal scan readings**
* Extracts **embedded images**
* Filters decorative or irrelevant images

Technologies:

* PyMuPDF
* Pillow

---

## AI Document Analysis

Uses **Google Gemini API** to analyze inspection + thermal reports.

AI generates:

* Property issue summary
* Area-wise observations
* Root cause analysis
* Recommended actions
* Additional notes

---

## Severity Scoring Engine

If AI does not provide severity, the system uses a **rule-based severity engine**.

Severity levels:

* Low
* Medium
* High
* Critical

Factors used:

* Moisture spread
* Structural damage
* Active leakage
* Thermal confirmation

---

## Image Mapping System

Inspection and thermal images are automatically linked to observations.

Example:

```
Observation: Bathroom tile leakage
Images: inspection_p4_img2, inspection_p4_img3
```

Images appear directly in the DDR report.

---

## HTML Diagnostic Report Generation

The system generates a **professional styled HTML report** including:

* Property issue summary
* Area observations
* Root causes
* Severity assessment
* Recommended actions
* Linked inspection images
* Thermal confirmation notes

Report is generated using:

* Jinja2 templates
* Structured DDR JSON

---

## Streamlit Web Interface

Users can run the system through a simple UI.

Workflow:

1 Upload inspection report
2 Upload thermal report
3 Generate DDR report
4 Download HTML report

---

# Architecture

```
Inspection PDF
        │
        ▼
PDF Extractor (PyMuPDF)
        │
        ├── Extract text
        └── Extract images
        │
        ▼
Data Normalizer
        │
        ▼
AI Analyzer (Gemini)
        │
        ▼
Severity Engine
        │
        ▼
Image Mapper
        │
        ▼
DDR JSON
        │
        ▼
Report Builder (Jinja2)
        │
        ▼
HTML Diagnostic Report
```

---

# Project Structure

```
ddr-ai-report-generator
│
├── main.py
├── ui.py
├── .env
├── .gitignore
├── README.md
│
├── inputs/
│   sample_inspection.pdf
│   sample_thermal.pdf
│
├── outputs/
│   extracted_images/
│   ddr_report.html
│
├── templates/
│   ddr_template.html
│
└── src/
    extractor.py
    analyzer.py
    normalizer.py
    severity_engine.py
    image_mapper.py
    schema.py
    report_builder.py
    utils.py
```

---

# Installation

## 1 Clone the repository

```
git clone https://github.com/ItzVirAj/ddr-ai-report-generator.git
cd ddr-ai-report-generator
```

---

## 2 Create Python environment

Recommended:

```
python -m venv ddr_env
```

Activate environment

Windows:

```
ddr_env\Scripts\activate
```

Linux/Mac:

```
source ddr_env/bin/activate
```

---

## 3 Install dependencies

```
pip install pymupdf pillow jinja2 python-dotenv google-genai streamlit
```

---

## 4 Configure Gemini API

Create `.env` file in project root:

```
GEMINI_API_KEY=your_api_key_here
```

Get API key from:

```
https://ai.google.dev/
```

---

# Usage

## Run via Streamlit UI (Recommended)

```
streamlit run ui.py
```

Open browser:

```
http://localhost:8501
```

Upload:

* Inspection report PDF
* Thermal report PDF

Click **Generate DDR Report**

---

## Run via CLI

```
python main.py --inspection inputs/sample_inspection.pdf --thermal inputs/sample_thermal.pdf
```

Output report:

```
outputs/ddr_report.html
```

---

# Example Output

Generated DDR includes:

```
Property Issue Summary
Area Observations
Root Cause Analysis
Severity Assessment
Recommended Actions
Inspection Images
Thermal Confirmation
```

Example observation:

```
Area: Master Bedroom

Observation:
Persistent dampness observed at skirting level indicating
moisture migration from adjacent wet areas.

Source:
Inspection + Thermal
```

---

# Current Limitations

## Image Mapping

Image-to-observation linking is based on **keyword matching**.

Future improvement:
Computer vision based mapping.

---

## Observation Grouping

LLM sometimes merges multiple rooms into one observation.

Example:

```
Hall, Bedroom, Kitchen
```

Future improvement:
Area detection preprocessing.

---

## Thermal Data Interpretation

Thermal scans are used as **supporting evidence**, not full analysis.

Future improvement:
Thermal anomaly detection.

---

## Report Format

Current output is **HTML only**.

Future improvement:
PDF export with formatting.

---

# Future Improvements

Planned upgrades:

### Vision AI Analysis

Use Gemini Vision to analyze inspection photos directly.

### Moisture Risk Scoring

Quantify moisture probability using thermal delta.

### Automatic Area Detection

Extract room names automatically.

### Professional PDF Reports

Generate engineer-grade reports.

### Dashboard System

Multi-property inspection dashboard.

---

# Technologies Used

Python
Google Gemini API
PyMuPDF
Pillow
Jinja2
Streamlit
dotenv

---

# Author

Viraj Mane

AI Developer | DevOps Enthusiast

---

# License

MIT License
