import sys
import time
import webbrowser
import threading
import uvicorn
from backend.config import HOST, PORT

def open_browser():
    """Wait for server to spin up and open web browser automatically."""
    time.sleep(1.5)
    url = f"http://localhost:{PORT}"
    print(f"\n=======================================================")
    print(f"🚀 FlashKlap AI is running!")
    print(f"🌐 Opening in your browser: {url}")
    print(f"⚡ Press Ctrl+C in this terminal to stop.")
    print(f"=======================================================\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass

if __name__ == "__main__":
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("backend.app:app", host=HOST, port=PORT, reload=False)

