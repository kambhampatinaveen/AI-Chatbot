# 🤖 AI Chatbot

An AI-powered chatbot web application built using **Python**, **Flask**, **SQLite**, **HTML**, **CSS**, and the **Groq API**. The chatbot provides intelligent conversational responses through a simple and responsive web interface while storing chat history in a local SQLite database.

---

## 📌 Features

- AI-powered chatbot using Groq LLM
- Clean and responsive user interface
- Stores chat history in SQLite database
- REST API using Flask
- Easy to configure and run locally
- Lightweight and beginner-friendly project

---

## 🛠️ Tech Stack

### Frontend
- HTML5
- CSS3
- JavaScript

### Backend
- Python
- Flask

### Database
- SQLite

### AI Model
- Groq API
- Llama 3.1 (Default Model)

---

## 📂 Project Structure

```
AI Chatbot/
│
├── app.py                # Flask Backend
├── chatbot.db            # SQLite Database
├── index.html            # Frontend
├── styles.css            # Styling
├── requirements.txt      # Project Dependencies
└── README.md             # Documentation
```

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/AI-Chatbot.git
```

### 2. Navigate to Project Folder

```bash
cd AI-Chatbot
```

### 3. Create Virtual Environment

Windows

```bash
python -m venv .venv
```

Activate Virtual Environment

```bash
.venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Run the Application

```bash
python app.py
```

Open your browser and visit

```
http://127.0.0.1:5000
```

---

## 📦 Requirements

- Python 3.10+
- Flask
- Requests

Install all dependencies using:

```bash
pip install -r requirements.txt
```

---

## 💾 Database

The application uses **SQLite** for storing chat history.

Database file:

```
chatbot.db
```

No additional database configuration is required.

---

## 📸 Application Workflow

1. User opens the chatbot.
2. User enters a message.
3. Flask backend receives the request.
4. Backend sends the prompt to the Groq API.
5. AI generates a response.
6. Response is displayed on the webpage.
7. Conversation is stored in SQLite.

---

## 🚀 Future Enhancements

- User Authentication
- Dark Mode
- Voice Input
- Speech-to-Text
- Text-to-Speech
- Multiple AI Models
- Conversation Export
- Chat History Dashboard

---

## 📄 License

This project is created for learning and educational purposes.

GitHub: https://github.com/kambhampatinaveen
