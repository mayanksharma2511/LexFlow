from fastapi import FastAPI

app = FastAPI(
    title="LexFlow API",
    description="Backend API for LexFlow",
    version="1.0.0",
)

@app.get("/")
def root():
    return {
        "project": "LexFlow",
        "version": "1.0.0",
        "status": "Running",
        "message": "Welcome to LexFlow 🚀"
    }