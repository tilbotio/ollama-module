import json
import multiprocessing
import os

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from ollama import chat
from typing import Any, Dict
from uvicorn import run

load_dotenv()

MODEL = os.getenv("MODEL", None)
PORT = int(os.getenv("PORT", 8081))

app = FastAPI()


def parse_history(messages: str | None) -> list[Dict[str, str]]:
    """Parse the chat history sent by Tilbot: a JSON list of {"role", "content"}."""
    if not messages:
        return []
    try:
        parsed = json.loads(messages)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [
        {"role": m["role"], "content": m["content"]}
        for m in parsed
        if isinstance(m, dict)
        and m.get("role") in ("user", "assistant")
        and isinstance(m.get("content"), str)
    ]

@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}

@app.post("/")
async def get_ollama_response(image: UploadFile = File(None),
    user_input: str = Form(""),
    prompt: str | None = Form(None),
    intent_options: str | None = Form(None),
    key_user_account: str | None = Form(None),
    messages: str | None = Form(None),
):

    intent_options_parsed = json.loads(intent_options) if intent_options else []
    history = parse_history(messages)

    prompt_message = [{"role": "system", "content": prompt}] if prompt else []
    if len(intent_options_parsed) > 0:
        prompt_message = [{"role": "system", "content": f"Find the best matching intent from the provided options: {intent_options_parsed}. If none match, return 'unknown'."}]
    total_messages = prompt_message + [{"role": "user", "content": user_input}]
    model_input = history + total_messages if history else total_messages

    print(model_input)

    if len(intent_options_parsed) > 0:
        print(f"Intent options provided: {intent_options_parsed}")
            
        response_format = {
            "type": "object",
            "properties": {
                "intent": {
                    "type": "string",
                    "enum": intent_options_parsed,
                    "description": "The best matching intent from the provided options."
                }
            },
            "required": ["intent"]
        }

        response = chat(
            model=MODEL,
            messages=model_input,
            format=response_format
        )

        results = json.loads(response.message.content)
        print(results)
        if results["intent"] not in intent_options_parsed or results["intent"] == "unknown":
            return None
        else:
            return {"intent": results["intent"], "connector_label": results["intent"]}
    else:
        response = chat(
            model=MODEL,
            messages=model_input
        )

        return {"intent": response.message.content, "connector_label": response.message.content}

if __name__ == "__main__":
    multiprocessing.freeze_support()  # For Windows support
    run(app, host="0.0.0.0", port=PORT, reload=False, workers=1)
