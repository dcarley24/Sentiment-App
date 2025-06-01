# Sentiment Analysis App (btf2)

This is a lightweight Flask-based web application for analyzing the sincerity of social media posts. It supports video and text uploads, applies transcription and sentiment scoring, and visualizes results with lexical and readability metrics.

## Features

- 🎥 Upload text or video files (MP4, MOV, AVI)
- 🔊 Automatic transcription using OpenAI Whisper
- 📊 Sentiment scoring via VADER (NLTK)
- 📚 Readability analysis with Textstat
- 📈 Lexical diversity and verbosity metrics
- 📂 SQLite-backed storage and labeling
- 🖼️ Results visualization with compact UI
- 🧠 Composite sincerity score (0–10 scale)

## Technologies Used

- Python 3.10+
- Flask
- OpenAI Whisper
- NLTK (VADER, stopwords)
- Textstat
- SQLite
- HTML/CSS (Tailwind for UI)
- Threading for async transcription

## Run the App

Create a virtual environment and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py

btf2/
│
├── app.py                 # Main Flask app
├── templates/             # HTML templates
├── static/                # JS/CSS and uploaded frames
├── uploads/               # Uploaded files
├── posts.db               # SQLite database
├── transcription_progress.json
├── requirements.txt
└── README.md
