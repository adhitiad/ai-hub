import json
import logging
import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# Inisialisasi Groq Client
# Pastikan GROQ_API_KEY ada di .env
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def consult_groq_analyst(symbol, asset_info, signal_data, whale_data):
    """
    Mengirim data pasar ke Groq AI untuk meminta 'Second Opinion'
    dan simulasi Profit/Loss.
    """

    # 1. Susun Laporan untuk AI
    system_prompt = """
    You are a Senior Hedge Fund Risk Manager. Your job is to validate trading signals detected by algorithms.
    You must output ONLY valid JSON. No yapping.
    
    Analyze the situation and decide:
    1. Should we FOLLOW the whale/bandar? (ACTION: FOLLOW / WAIT)
    2. Why? (Reasoning)
    3. Calculate Estimated Profit in currency (Based on TP and Lot Size)
    4. Calculate Estimated Loss in currency (Based on SL and Lot Size)
    
    JSON Format:
    {
        "decision": "FOLLOW" or "WAIT",
        "reason": "Brief explanation...",
        "est_profit": "Value + Currency",
        "est_loss": "Value + Currency",
        "risk_score": 1-10
    }
    """

    user_content = f"""
    ASSET: {symbol}
    TYPE: {asset_info.get('type')}
    CURRENT PRICE: {signal_data['Price']}
    PROPOSED ACTION: {signal_data['Action']}
    LOT SIZE: {signal_data.get('LotSize', 'Unknown')}
    
    TECHNICALS:
    - TP Level: {signal_data['Tp']}
    - SL Level: {signal_data['Sl']}
    
    WHALE/BANDAR DATA:
    - Type: {whale_data.get('type') or whale_data.get('status')}
    - Message: {whale_data.get('message') or whale_data.get('Analysis')}
    - Strength/Score: {whale_data.get('strength') or whale_data.get('Score')}
    
    Analyze now.
    """

    # 2. Kirim ke Groq (Model Llama3-70b sangat cepat & pintar)
    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.2,  # Rendah agar jawaban konsisten/faktual
            response_format={"type": "json_object"},  # Memaksa output JSON
        )

        # 3. Parse Jawaban
        content = completion.choices[0].message.content
        if content is None:
            raise ValueError("Groq response content is empty")
        result = json.loads(content)
        logging.info(f"Groq Response: {result}")
        return result

    except Exception as e:
        logging.error(f"Groq Error: {e}")
        # Fallback jika AI error
        return {
            "decision": "FOLLOW",  # Default follow algo
            "reason": "AI Analyst unavailable, falling back to algorithm.",
            "est_profit": "Calc by System",
            "est_loss": "Calc by System",
            "risk_score": 5,
        }


def ai_fix_code(code_content, error_message):
    """
    Mengirim kode rusak ke AI untuk diperbaiki syntax-nya.
    """
    system_prompt = """
    You are a Python Expert. 
    Your task is to FIX the Syntax Error in the provided Python code.
    Do NOT change the logic. Only fix indentation, missing colons, parenthesis, etc.
    Output ONLY the fixed code. No markdown, no explanations.
    """

    user_content = f"""
    ERROR: {error_message}
    
    BROKEN CODE:
    {code_content}
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.1,  # Sangat rendah agar presisi
        )

        # Bersihkan output (kadang AI kasih ```python ... ```)
        fixed_code = completion.choices[0].message.content
        if fixed_code is None:
            return None
        fixed_code = fixed_code.replace("```python", "").replace("```", "").strip()

        return fixed_code
    except (ValueError, AttributeError):
        return None
