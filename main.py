import sqlite3
import os
import json
from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI

# Pobieramy klucz bezpiecznie
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

# -----------------------------
# INICJALIZACJA BAZY
# -----------------------------

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT,
            intent TEXT,
            address TEXT,
            phone TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()

# -----------------------------
# AI EKSTRAKCJA
# -----------------------------

def extract_data_with_ai(text):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
                Jesteś systemem ekstrakcji danych zgłoszenia serwisowego.

                Wyciągnij z tekstu:
                - intent (np. awaria, reklamacja)
                - device (np. pralka, lodówka, piec)
                - address
                - phone

                Zwróć WYŁĄCZNIE JSON:
                {
                  "intent": string or null,
                  "device": string or null,
                  "address": string or null,
                  "phone": string or null
                }
                """
            },
            {
                "role": "user",
                "content": text
            }
        ],
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)


# -----------------------------
# MODEL
# -----------------------------

class Message(BaseModel):
    conversation_id: str
    text: str

conversation_states = {}

# -----------------------------
# ROOT
# -----------------------------

@app.get("/")
def root():
    return {"message": "API działa poprawnie"}

# -----------------------------
# ENDPOINT ROZMOWY
# -----------------------------

@app.post("/message")
def handle_message(message: Message):
    conv_id = message.conversation_id
    text = message.text

    ai_data = extract_data_with_ai(text)

    if conv_id not in conversation_states:
        conversation_states[conv_id] = {
    "intent": None,
    "device": None,
    "address": None,
    "phone": None
}


    state = conversation_states[conv_id]

    # Aktualizacja state z AI
    if ai_data.get("intent"):
        state["intent"] = ai_data["intent"]

    if ai_data.get("address"):
        state["address"] = ai_data["address"]

    if ai_data.get("phone"):
        state["phone"] = ai_data["phone"]

    if ai_data.get("device"):
        state["device"] = ai_data["device"]


    # Sprawdzenie czy mamy komplet danych
    if state["intent"] and state["address"] and state["phone"]:

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO tickets (conversation_id, intent, address, phone)
            VALUES (?, ?, ?, ?)
        """, (conv_id, state["intent"], state["address"], state["phone"]))

        conn.commit()
        conn.close()

        return {
            "response": "Dziękujemy. Zgłoszenie zostało przyjęte.",
            "ticket_data": state
        }

    # Braki
    missing = []
    if not state["intent"]:
        missing.append("opis problemu")
    if not state["address"]:
        missing.append("adres")
    if not state["phone"]:
        missing.append("numer telefonu")

    return {
        "response": f"Proszę podać: {', '.join(missing)}.",
        "current_state": state
    }

# -----------------------------
# PODGLĄD TICKETÓW
# -----------------------------

@app.get("/tickets")
def get_tickets():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tickets")
    rows = cursor.fetchall()

    conn.close()

    return {"tickets": rows}