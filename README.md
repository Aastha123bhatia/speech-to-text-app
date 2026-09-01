# 🎤 Bilingual Voice Transcriber

A simple and user-friendly Speech-to-Text web application built using Python, Streamlit, and Faster-Whisper.

The application allows users to record their voice and convert speech into text. It supports both English and Hindi, automatically detects the spoken language, displays a confidence score, allows transcript editing, downloading, and maintains transcription history.

---

## 🚀 Features

- 🎙️ Record voice directly from the browser
- 🌐 Automatic English and Hindi language detection
- 📝 Convert speech into text
- 📊 Display language confidence score
- ✏️ Edit generated transcript
- 📋 Copy transcript
- 🔤 Word and character count
- 📄 Download transcript as TXT
- 📋 Download transcript as JSON
- 📚 Save transcription history
- 🔎 Search transcription history
- 🌐 Filter history by language
- 📥 Download individual history entries
- 🗑️ Delete individual history entries
- 🗑️ Delete all history with confirmation
- 🔄 Start a new recording without deleting saved history
- 📱 Responsive Streamlit interface

---

## 🛠️ Technologies Used

- Python
- Streamlit
- Faster-Whisper
- Whisper Speech Recognition Model

---

## 📂 Project Structure

```text
speech-to-text-app/
│
├── speech/
│   ├── __init__.py
│   └── recognizer.py
│
├── transcripts/
│   └── .gitkeep
│
├── app.py
├── requirements.txt
├── .gitignore
└── README.md