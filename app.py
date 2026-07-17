import os
import sqlite3
import requests
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory, Response

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "chatbot.db"
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
app = Flask(__name__, static_folder=str(BASE_DIR))


def init_db():
    with sqlite3.connect(DB_PATH, timeout=30) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS chats (id TEXT PRIMARY KEY, title TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, pinned INTEGER DEFAULT 0, persona TEXT DEFAULT 'general')"
        )
        try:
            conn.execute("ALTER TABLE chats ADD COLUMN persona TEXT DEFAULT 'general'")
        except sqlite3.OperationalError:
            pass
        conn.execute(
            "CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id TEXT NOT NULL, role TEXT NOT NULL, text TEXT NOT NULL, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (chat_id) REFERENCES chats(id))"
        )


def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


SYSTEM_PROMPT_TEMPLATES = {
    "teacher": "You are a friendly, patient, and encouraging teacher AI assistant. Explain concepts clearly, break down complex topics into easy-to-understand steps, use analogies, and ask guiding questions to help the user learn.",
    "coder": "You are an elite senior software engineer and coding expert AI assistant. Provide highly optimized, clean, safe, and modern code solutions. Explain your logic concisely, point out potential edge cases, and follow best practices in software design.",
    "general": "You are a helpful, clear, and direct AI assistant for a web chatbot. Answer clearly and directly. If the user asks for facts that may have changed after your knowledge cutoff, say that plainly instead of pretending you have live browsing.",
}


def build_groq_messages(history, latest_message, persona="general"):
    system_content = f"{SYSTEM_PROMPT_TEMPLATES.get(persona, SYSTEM_PROMPT_TEMPLATES['general'])} Today's date is {datetime.now().strftime('%B %d, %Y')}."
    messages = [{"role": "system", "content": system_content}]
    for item in history[-12:]:
        text = (item.get("text") or "").strip()
        if text:
            role = "assistant" if item.get("role") in {"assistant", "bot"} else "user"
            messages.append({"role": role, "content": text})
    if not messages or messages[-1]["role"] != "user":
        messages.append({"role": "user", "content": latest_message})
    return messages


init_db()


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    return response


@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/styles.css")
def styles():
    return send_from_directory(BASE_DIR, "styles.css")


@app.route("/api/chats")
def get_chats():
    conn = get_db_connection()
    chats = [
        dict(c)
        for c in conn.execute(
            "SELECT * FROM chats ORDER BY pinned DESC, updated_at DESC LIMIT 50"
        )
    ]
    for c in chats:
        c["messages"] = [
            dict(m)
            for m in conn.execute(
                "SELECT role, text FROM messages WHERE chat_id = ? ORDER BY timestamp, id",
                (c["id"],),
            )
        ]
    conn.close()
    return jsonify(chats)


@app.route("/api/chat/save", methods=["POST"])
def save_chat():
    payload = request.get_json(silent=True) or {}
    chat_id = payload.get("id")
    if not chat_id:
        return jsonify({"error": "Chat ID is required"}), 400

    title = (payload.get("title") or "New conversation").strip() or "New conversation"
    pinned = 1 if payload.get("pinned") else 0
    persona = payload.get("persona") or "general"

    conn = get_db_connection()
    conn.execute(
        "INSERT OR IGNORE INTO chats (id, title, pinned, persona) VALUES (?, ?, ?, ?)",
        (chat_id, title, pinned, persona),
    )
    conn.execute(
        "UPDATE chats SET title = ?, updated_at = CURRENT_TIMESTAMP, pinned = ?, persona = ? WHERE id = ?",
        (title, pinned, persona, chat_id),
    )
    conn.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))

    messages = [
        (chat_id, m.get("role"), m.get("text").strip())
        for m in payload.get("messages") or []
        if m.get("role") and (m.get("text") or "").strip()
    ]
    if messages:
        conn.executemany(
            "INSERT INTO messages (chat_id, role, text) VALUES (?, ?, ?)", messages
        )

    conn.commit()
    conn.close()
    return jsonify({"success": True, "id": chat_id})


@app.route("/api/chat/delete/<chat_id>", methods=["DELETE"])
def delete_chat(chat_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
    conn.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/chat/pin/<chat_id>", methods=["POST"])
def pin_chat(chat_id):
    pinned = 1 if (request.get_json(silent=True) or {}).get("pinned") else 0
    conn = get_db_connection()
    conn.execute("UPDATE chats SET pinned = ? WHERE id = ?", (pinned, chat_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/chat", methods=["POST"])
def chat():
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Please enter a message."}), 400

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": build_groq_messages(
                    payload.get("messages") or [],
                    message,
                    payload.get("persona") or "general",
                ),
                "temperature": 0.7,
                "stream": True,
            },
            stream=True,
            timeout=60,
        )
        if response.status_code != 200:
            return jsonify(
                {"error": f"Groq API error: {response.text}"}
            ), response.status_code
        return Response(
            (line + b"\n" for line in response.iter_lines() if line),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


def get_bool_env(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000")),
        debug=get_bool_env("FLASK_DEBUG", True),
        use_reloader=False,
        threaded=True,
    )
