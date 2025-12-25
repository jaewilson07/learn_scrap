import uvicorn
from legendary_potato.app.main import app
from pyngrok import ngrok
import threading
import time

from dotenv import load_dotenv

assert load_dotenv()


def run_uvicorn():
    uvicorn.run(app, host="0.0.0.0", port=8001)


if __name__ == "__main__":
    uvicorn_thread = threading.Thread(target=run_uvicorn)
    uvicorn_thread.daemon = True
    uvicorn_thread.start()
    time.sleep(2)  # Give uvicorn a moment to start

    # Open a tunnel to the uvicorn server
    public_url = ngrok.connect(8001)
    print(f"Public URL: {public_url}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        ngrok.disconnect(public_url)
        print("ngrok tunnel closed.")
