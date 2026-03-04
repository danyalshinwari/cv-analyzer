# 🔮 Resume Intelligence AI

**Resume Intelligence AI** is an advanced Applicant Tracking System (ATS), career optimization hub, and interview intelligence laboratory. Powered by Google Gemini 1.5 Flash and a comprehensive NLP scoring system, this Streamlit application empowers job seekers to maximize their chances of securing their dream roles. 

## ✨ Key Features

* **⚡ Analysis Engine:** Upload a resume (PDF) and a Job Description (JD). The AI engine parses both, compares them structurally and semantically, and returns a detailed Match Score. It extracts missing skills, offers actionable improvement tips, and visually highlights metric breakdowns using beautiful Streamlit Echarts gauges. You can even generate a Neural Profile Branding aesthetic!
* **🏆 Bulk Ranker:** Compare multiple candidate resumes against a single Job Description simultaneously. Output generates a polished candidate leaderboard, categorized by performance tiers.
* **✉️ Tailored Cover Letter Generator:** Input your resume and a JD, and the AI crafts a completely customized, high-converting professional cover letter compliant with international formal business standards.
* **🎙️ Interview Lab (Voice & Text):** Automatically generates specialized, challenging interview questions based *specifically* on your resume and the target JD. Use the built-in microphone (or upload audio) to practice and receive real-time AI feedback on your speech clarity, pacing, and words!
* **📜 Analysis History:** All parsed metrics and results are stored securely in a local SQLite database that you can reload at any time.

## 🚀 Setting Up the Application Locally

### 1. Requirements

Ensure you have Python 3.9+ installed on your machine.

### 2. Installation

Clone this repository and navigate to the project root directory:

```bash
git clone https://github.com/your-username/cv-analyzer-ai.git
cd cv-analyzer-ai
```

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 3. Environment Variables

Create a `.env` file in the root directory and add your Google Gemini API Key:

```env
GOOGLE_API_KEY="your-gemini-api-key-here"
```

> **Note:** The application features a built-in Mock Mode (`MOCK_MODE=True` in `config.py`) that falls back to a fast, locally run offline NLP NLP system if you do not provide a valid API key!

### 4. Running the App

To run the application locally, start the built-in Streamlit server:

```bash
python -m streamlit run app.py
```

Open `http://localhost:8501` in your browser to view the application!

## 📦 Project Structure

```
├── app.py                   # Main Streamlit application
├── config.py                # App configuration variables
├── requirements.txt         # Project dependencies
├── models/
│   └── gemini_analyzer.py    # Core intelligence & Gemini AI connectivity
├── utils/
│   ├── dataset_loader.py    # Logic for offline keyword/dataset matching
│   ├── history_db.py        # SQLite history operations
│   ├── pdf_generator.py     # Downloadable PDF report generation
│   ├── prompts.py           # Formal prompt configurations
│   ├── scraper.py           # JD web-scraping utilities
│   ├── text_extractor.py    # PDF Plumber resume extractor
│   └── voice_evaluator.py   # Speech recognition module
└── README.md                # Project documentation
```

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

## 📝 License

This project is licensed under the [MIT License](LICENSE).
