# ai_engine.py
import logging
import requests
import google.generativeai as genai
from groq import Groq
import config
from database import log_engine_metric

# Configure production-grade logging registry
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Primary Multimodal Engine (Google Gemini)
if config.GEMINI_API_KEY and "YOUR_SECRET" not in config.GEMINI_API_KEY:
    genai.configure(api_key=config.GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=config.SYSTEM_PROMPT
    )
else:
    gemini_model = None

# Initialize Secondary Text Fallback Engine (Groq)
groq_client = Groq(api_key=config.GROQ_API_KEY) if (config.GROQ_API_KEY and "YOUR_SECRET" not in config.GROQ_API_KEY) else None

def process_multimodal_request(prompt_text: str, mime_type: str = None, media_data: bytes = None, chat_history: list = None) -> str:
    if not gemini_model:
        if not media_data:
            return _fallback_text_chain(prompt_text)
        return "❌ Critical Error: Primary AI Engine Key is unconfigured."

    try:
        logger.info("🤖 Routing request to Multimodal Engine: Gemini API")
        context_payload = []
        if chat_history:
            for interaction in chat_history:
                prefix = "User" if interaction['role'] == "user" else "Model"
                context_payload.append(f"{prefix}: {interaction['content']}")
        
        # Fixed: Wrapping raw media bytes into proper inline_data structure for Gemini SDK
        if media_data and mime_type:
            contents = [
                {"inline_data": {"mime_type": mime_type, "data": media_data}},
                f"Conversation History:\n" + "\n".join(context_payload) + f"\n\nCurrent Request:\n{prompt_text if prompt_text else 'Analyze this uploaded file contextually.'}"
            ]
            response = gemini_model.generate_content(contents)
        else:
            final_prompt = f"Conversation History:\n" + "\n".join(context_payload) + f"\n\nCurrent Request:\n{prompt_text}"
            response = gemini_model.generate_content(final_prompt)

        if response and hasattr(response, "text") and response.text:
            log_engine_metric('Gemini', success=True) # Success Hook
            return response.text
        raise Exception("Gemini returned an empty or invalid content frame.")

    except Exception as e:
        logger.error(f"Primary Multimodal Engine Failed: {str(e)}")
        log_engine_metric('Gemini', success=False) # Failure Hook
        if not media_data:
            return _fallback_text_chain(prompt_text)
        return "⚠️ Error: The AI Server is currently unable to process media files. Please try again shortly."

def _fallback_text_chain(text: str) -> str:
    # 1. Secondary Fallback: Groq API
    try:
        if groq_client:
            logger.info("🚀 Falling back to Secondary Text Engine: Groq API (Llama 3.3)")
            chat = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": config.SYSTEM_PROMPT},
                    {"role": "user", "content": text}
                ],
                model="llama-3.3-70b-versatile"
            )
            log_engine_metric('Groq', success=True)
            return chat.choices[0].message.content
    except Exception as e:
        logger.warning(f"Groq Text Fallback Failed: {str(e)}")
        log_engine_metric('Groq', success=False)

    # 2. Tertiary Fallback: OpenRouter API
    try:
        if config.OPENROUTER_API_KEY and "YOUR_SECRET" not in config.OPENROUTER_API_KEY:
            logger.info("⚠️ Falling back to Tertiary Text Engine: OpenRouter API")
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {"Authorization": f"Bearer {config.OPENROUTER_API_KEY}", "Content-Type": "application/json"}
            data = {
                "model": "meta-llama/llama-3.1-8b-instruct:free",
                "messages": [
                    {"role": "system", "content": config.SYSTEM_PROMPT},
                    {"role": "user", "content": text}
                ]
            }
            res = requests.post(url, headers=headers, json=data, timeout=12)
            if res.status_code == 200:
                log_engine_metric('OpenRouter', success=True)
                return res.json()['choices'][0]['message']['content']
        log_engine_metric('OpenRouter', success=False)
    except Exception as e:
        logger.warning(f"OpenRouter Fallback Failed: {str(e)}")
        log_engine_metric('OpenRouter', success=False)

    # 3. Quaternary Fallback: Together AI
    try:
        if config.TOGETHER_API_KEY and "YOUR_SECRET" not in config.TOGETHER_API_KEY:
            logger.info("⚠️ Falling back to Quaternary Text Engine: Together AI")
            url = "https://api.together.xyz/v1/chat/completions"
            headers = {"Authorization": f"Bearer {config.TOGETHER_API_KEY}", "Content-Type": "application/json"}
            data = {
                "model": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
                "messages": [
                    {"role": "system", "content": config.SYSTEM_PROMPT},
                    {"role": "user", "content": text}
                ]
            }
            res = requests.post(url, headers=headers, json=data, timeout=12)
            if res.status_code == 200:
                log_engine_metric('TogetherAI', success=True)
                return res.json()['choices'][0]['message']['content']
        log_engine_metric('TogetherAI', success=False)
    except Exception as e:
        logger.warning(f"Together AI Fallback Failed: {str(e)}")
        log_engine_metric('TogetherAI', success=False)

    return "⚠️ System Congestion: All active fallback AI cores are currently unresponsive. Please retry later."
