import discord
import os
import asyncio
from openai import AsyncOpenAI
from google import genai
from dotenv import load_dotenv

# Lädt die Umgebungsvariablen aus der .env Datei
load_dotenv()

# --- KONFIGURATION ---
# Die ID des Kanals, in den der Puffer-Inhalt gesendet wird
TARGET_CHANNEL_ID = 1439563178940956714  
# Pfad zur Puffer-Datei
PUFFER_FILE = r"C:\Users\eteck\OneDrive\Desktop\Hallo-Support\puffer.txt"

# Discord Intents (Berechtigungen)
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# API Keys aus der .env laden
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")

# Clients initialisieren
openai_client = None
gemini_client = None

if OPENAI_API_KEY:
    openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
if GEMINI_API_KEY:
    # Hinweis: Falls dein spezielles Modell "gemini-2.5-flash" heißt, 
    # stelle sicher, dass die Library aktuell ist.
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# --- FUNKTION: PUFFER-DATEI ÜBERWACHUNG ---
async def check_puffer_file():
    """Prüft sekündlich die puffer.txt und sendet den Inhalt an Discord"""
    await client.wait_until_ready()
    channel = client.get_channel(TARGET_CHANNEL_ID)
    
    if not channel:
        print(f"[FEHLER] Kanal {TARGET_CHANNEL_ID} wurde nicht gefunden!")
        return

    print(f"[*] Puffer-Überwachung gestartet für: {PUFFER_FILE}")

    while not client.is_closed():
        if os.path.exists(PUFFER_FILE):
            try:
                # Datei mit UTF-8 lesen, um Umlaute zu unterstützen
                with open(PUFFER_FILE, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                
                if content:
                    await channel.send(content)
                    print(f"[Extern gesendet]: {content}")
                
                # Datei löschen, um doppeltes Senden zu verhindern
                os.remove(PUFFER_FILE)
            except Exception as e:
                print(f"[Fehler beim Puffer-Verarbeiten]: {e}")
        
        await asyncio.sleep(1)

# --- KI FUNKTIONEN ---
async def get_ai_response(question):
    """Versucht erst OpenAI, dann Gemini als Backup"""
    
    # 1. Versuch: ChatGPT
    if openai_client:
        try:
            resp = await openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": question}],
                max_tokens=500
            )
            return f"[ChatGPT] {resp.choices[0].message.content}"
        except Exception as e:
            print(f"[OpenAI Fehler]: {e}")
    
    # 2. Versuch: Gemini
    if gemini_client:
        try:
            # Da die genai-Library oft synchron ist, führen wir sie in einem Executor aus
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(None, lambda: gemini_client.models.generate_content(
                model="gemini-2.0-flash", contents=question))
            return f"[Gemini] {resp.text}"
        except Exception as e:
            print(f"[Gemini Fehler]: {e}")
    
    return "❌ Keine KI antwortet gerade. Bitte API-Keys und Internetverbindung prüfen."

# --- DISCORD EVENTS ---
@client.event
async def on_ready():
    print(f'--- {client.user} ist jetzt online ---')
    # Startet die Puffer-Überwachung als Hintergrundaufgabe
    client.loop.create_task(check_puffer_file())

@client.event
async def on_message(message):
    # Ignoriere Nachrichten vom Bot selbst
    if message.author == client.user:
        return
    
    # Befehl für KI-Anfragen: /bot [Frage]
    if message.content.startswith('/bot '):
        question = message.content[5:].strip()
        
        if not question:
            await message.channel.send("Bitte gib eine Frage ein!")
            return

        # "Ich überlege..." Nachricht senden und später editieren
        thinking_msg = await message.channel.send("⏳ Ich überlege...")
        
        answer = await get_ai_response(question)
        
        # Die ursprüngliche Nachricht mit der Antwort überschreiben
        await thinking_msg.edit(content=answer)

# --- BOT START ---
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("CRITICAL ERROR: DISCORD_TOKEN nicht in der .env gefunden!")
    else:
        client.run(DISCORD_TOKEN)