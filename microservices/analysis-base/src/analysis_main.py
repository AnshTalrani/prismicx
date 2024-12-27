from fastapi import FastAPI

app = FastAPI()

@app.get("/analyze")
def analyze():
    return {"analysis": "Basic analysis result"}
