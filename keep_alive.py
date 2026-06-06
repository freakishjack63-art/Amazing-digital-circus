import os
from flask import Flask
from threading import Thread

app = Flask("")

@app.route("/")
def home():
    return "The Amazing Digital Circus bot is alive!"

@app.route("/health")
def health():
    return "OK", 200

def run():
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()