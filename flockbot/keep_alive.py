"""
Keep-Alive Service for Discord Bot Hosting
This prevents the bot from sleeping on free hosting platforms
"""

from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!", 200

def run():
    """Run the Flask server in a separate thread"""
    try:
        app.run(host='0.0.0.0', port=8080)
    except Exception as e:
        print(f"Error running keep_alive server: {e}")

def start():
    """Start the keep_alive server"""
    server_thread = Thread(target=run, daemon=True)
    server_thread.start()
    print("Keep-alive server started on port 8080")
