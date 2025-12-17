# main.py
from fastapi import FastAPI

# Create the application instance
app = FastAPI()

# Define a "route"
@app.get("/")
def read_root():
    return {"message": "Hello World"}