import os
import json
import httpx
from typing import Optional
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from prompt_templates import BLOG_IDEA_PROMPT  # Ensure this is defined correctly

# Initialize FastAPI app
app = FastAPI(title="Blog Idea Generator")

# Set up templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configuration for AI APIs
WEBUI_ENABLED = True
WEBUI_BASE_URL = "https://chat.ivislabs.in/api"
API_KEY = os.getenv("WEBUI_API_KEY", "sk-ca217a4d09d64df7865427af8622c9b7")  # Replace with actual key
DEFAULT_MODEL = "gemma2:2b"

OLLAMA_ENABLED = True
OLLAMA_HOST = "localhost"
OLLAMA_PORT = "11434"
OLLAMA_API_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api"

class GenerationRequest(BaseModel):
    niche: str = Field(..., min_length=3, max_length=100, title="Niche")
    num_ideas: int = Field(3, ge=1, le=10, title="Number of Ideas")
    include_outline: bool = Field(True, title="Include Outline")
    tone: Optional[str] = Field("professional", title="Tone")
    model: str = Field(DEFAULT_MODEL, title="Model")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def generate_ideas(
    niche: str = Form(...),
    num_ideas: int = Form(3),
    include_outline: bool = Form(True),
    tone: str = Form("professional"),
    model: str = Form(DEFAULT_MODEL)
):
    # Debugging print statement to log received form data
    print(f"Received Form Data: niche={niche}, num_ideas={num_ideas}, include_outline={include_outline}, tone={tone}, model={model}")

    # Construct the prompt based on the received data
    prompt = BLOG_IDEA_PROMPT.format(niche=niche, num_ideas=num_ideas, include_outline=include_outline, tone=tone)

    # Try open-webui API first
    if WEBUI_ENABLED:
        response = await call_open_webui_api(prompt, model)
        if response:
            return {"generated_ideas": response}

    # Fallback to Ollama API
    if OLLAMA_ENABLED:
        response = await call_ollama_api(prompt, model)
        if response:
            return {"generated_ideas": response}

    raise HTTPException(status_code=500, detail="Failed to generate content from available LLMs")

async def call_open_webui_api(prompt: str, model: str) -> Optional[str]:
    try:
        messages = [{"role": "user", "content": prompt}]
        payload = {"model": model, "messages": messages}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{WEBUI_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
                json=payload,
                timeout=60
            )
        
        if response.status_code == 200:
            result = response.json()
            return extract_generated_text(result)
        else:
            print(f"Open-webui API Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Error calling open-webui API: {str(e)}")
    return None

async def call_ollama_api(prompt: str, model: str) -> Optional[str]:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OLLAMA_API_URL}/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=60
            )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "")
        else:
            print(f"Ollama API Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Error calling Ollama API: {str(e)}")
    return None

def extract_generated_text(api_response: dict) -> str:
    """Extracts generated text from API response, handling different formats."""
    if "choices" in api_response and api_response["choices"]:
        choice = api_response["choices"][0]
        return choice.get("message", {}).get("content", choice.get("text", ""))
    return api_response.get("response", "")

@app.get("/models")
async def get_models():
    """Fetch available models from APIs."""
    models = await fetch_webui_models() or await fetch_ollama_models()
    return {"models": models or [DEFAULT_MODEL]}

async def fetch_webui_models() -> Optional[list]:
    """Fetches models from open-webui API."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{WEBUI_BASE_URL}/models",
                headers={"Authorization": f"Bearer {API_KEY}"}
            )
        if response.status_code == 200:
            return [m["id"] for m in response.json().get("data", []) if "id" in m]
    except Exception as e:
        print(f"Error fetching models from open-webui API: {e}")
    return None

async def fetch_ollama_models() -> Optional[list]:
    """Fetches models from Ollama API."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_API_URL}/tags")
        if response.status_code == 200:
            return [m.get("name") for m in response.json().get("models", [])]
    except Exception as e:
        print(f"Error fetching models from Ollama API: {e}")
    return None

if __name__ == "__main__":
    import uvicorn
    # Run the application using the command below:
    # uvicorn main:app --reload --host 0.0.0.0 --port 8000
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
