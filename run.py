"""
AI Human Activity Recognition for On-board BAS Experiments
Unified Application Launcher (Backend + Frontend)
"""
import uvicorn
import webbrowser
import threading
import time

def open_browser():
    time.sleep(1.2)
    webbrowser.open("http://127.0.0.1:8080/")

if __name__ == "__main__":
    print("=" * 65)
    print("AI HUMAN ACTIVITY RECOGNITION FOR ON-BOARD BAS EXPERIMENTS")
    print("Standalone Edge AI Assistant for Microgravity Science")
    print("=" * 65)
    print(">> Starting local FastAPI server on http://127.0.0.1:8080...")
    print(">> Serving 3D WebGL Frontend, REST APIs, and WebSockets...")
    print(">> Press Ctrl+C to terminate.")
    print("=" * 65)

    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8080, log_level="info")
