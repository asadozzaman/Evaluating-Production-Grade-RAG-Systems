from dataclasses import dataclass
import time

import httpx

from app.config import Settings


@dataclass(frozen=True)
class GeminiAnswer:
    text: str
    model_name: str
    input_tokens: int | None
    output_tokens: int | None
    generation_time_ms: int


class GeminiClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate_answer(self, prompt: str) -> GeminiAnswer:
        api_key = normalize_secret(self.settings.gemini_api_key)
        if not api_key:
            raise RuntimeError("Gemini API key is missing. Set GEMINI_API_KEY in backend/.env and restart the backend.")

        model_name = normalize_model_name(self.settings.default_llm_model)
        url = f"{self.settings.gemini_api_base_url.rstrip('/')}/models/{model_name}:generateContent"
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.9,
            },
        }

        started = time.perf_counter()
        response = httpx.post(
            url,
            headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
            json=payload,
            timeout=45,
        )
        generation_time_ms = max(0, round((time.perf_counter() - started) * 1000))

        if response.status_code >= 400:
            raise RuntimeError(f"Gemini request failed with status {response.status_code}: {safe_error_text(response)}")

        data = response.json()
        text = extract_text(data)
        if not text:
            raise RuntimeError("Gemini returned an empty answer.")

        usage = data.get("usageMetadata", {})
        return GeminiAnswer(
            text=text,
            model_name=model_name,
            input_tokens=usage.get("promptTokenCount") or estimate_tokens(prompt),
            output_tokens=usage.get("candidatesTokenCount") or estimate_tokens(text),
            generation_time_ms=generation_time_ms,
        )


def normalize_model_name(model_name: str) -> str:
    stripped = model_name.strip()
    if stripped in {"gemini", "models/gemini"}:
        return "gemini-2.5-flash"
    return stripped.removeprefix("models/")


def normalize_secret(value: str | None) -> str:
    if not value:
        return ""
    return value.strip().strip('"').strip("'")


def extract_text(data: dict) -> str:
    candidates = data.get("candidates") or []
    if not candidates:
        return ""
    parts = candidates[0].get("content", {}).get("parts", [])
    return "\n".join(part.get("text", "") for part in parts).strip()


def estimate_tokens(value: str) -> int:
    return max(1, round(len(value.split()) * 1.3))


def safe_error_text(response: httpx.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        return response.text[:400]
    message = data.get("error", {}).get("message")
    return str(message or data)[:400]
