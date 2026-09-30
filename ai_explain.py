"""
Gemini AI Flash Model (Agentic LLM)
Flowchart step 5 -> "Request AI Delay Explanation & Action"

Turns the raw numbers from the Deviation Analytics Engine and the OSRM
detour into the plain-language decision card the operator sees on the
dashboard, e.g.:
  "Unit #04 delayed on Main St gridlock. Recommendation: Divert via
   Grand Ave (+3 min detour, avoids gridlock)."
"""
import google.generativeai as genai

from app.config import settings

_configured = False


def _ensure_configured():
    global _configured
    if not _configured:
        if not settings.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Add it to backend/.env "
                "(get a free key at https://aistudio.google.com/app/apikey)"
            )
        genai.configure(api_key=settings.gemini_api_key)
        _configured = True


PROMPT_TEMPLATE = """You are the agentic decision engine for an ambulance dispatch \
control room. Write a short, plain-language explanation for the human operator.

Vehicle call sign: {call_sign}
Distance off planned route: {distance_m:.0f} m
Likely cause: {cause}
Original ETA delay if no reroute: {delay_min} minutes
Suggested detour adds: {detour_min:.1f} minutes, avoiding the blockage

Reply in exactly two short sentences, in this style:
"Unit #04 delayed on Main St gridlock. Recommendation: Divert via Grand Ave \
(+3 min detour, avoids gridlock)."
Do not add any other text.
"""


def explain_deviation(call_sign: str, distance_m: float, cause: str,
                       delay_min: float, detour_min: float) -> str:
    """Returns the natural-language explanation string for the decision card.
    Falls back to a template string if no API key is configured, so the demo
    still runs end-to-end without Gemini access."""
    try:
        _ensure_configured()
        model = genai.GenerativeModel(settings.gemini_model)
        prompt = PROMPT_TEMPLATE.format(
            call_sign=call_sign, distance_m=distance_m, cause=cause,
            delay_min=delay_min, detour_min=detour_min,
        )
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as exc:  # noqa: BLE001 - demo fallback, log and degrade gracefully
        print(f"[ai_explain] Gemini call failed, using fallback text: {exc}")
        return (
            f"{call_sign} delayed on planned route ({cause}). "
            f"Recommendation: divert via suggested detour "
            f"(+{detour_min:.0f} min, avoids the blockage)."
        )
