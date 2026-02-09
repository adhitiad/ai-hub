import json
import logging
import os

from dotenv import load_dotenv
from groq import AsyncGroq

load_dotenv()


class LLMAnalyst:
    def __init__(self):
        """
        Inisialisasi Async Groq Client.
        Pastikan GROQ_API_KEY ada di .env
        """
        self.client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))

    async def generate_response(
        self,
        prompt: str,
        model: str = "meta-llama/llama-guard-4-12b",
        temperature: float = 1,
        is_json: bool = False,
    ) -> str | None:
        """
        Fungsi generik untuk mendapatkan respons dari LLM, mendukung output JSON.
        """
        try:
            response_format = {"type": "json_object"} if is_json else None

            completion = await self.client.chat.completions.create(
                model=model,
                messages=[
                    # Kita masukkan semua instruksi ke dalam user prompt untuk simplisitas
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                response_format=response_format,  # type: ignore
            )
            return completion.choices[0].message.content
        except Exception as e:
            logging.error(f"LLM generation failed: {e}")
            return None

    async def consult_groq_analyst(self, symbol, asset_info, signal_data, whale_data):
        """
        Mengirim data pasar ke Groq AI untuk meminta 'Second Opinion' (versi async).
        """
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
        try:
            completion = await self.client.chat.completions.create(
                model="meta-llama/llama-guard-4-12b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            content = completion.choices[0].message.content
            if content is None:
                raise ValueError("Groq response content is empty")
            result = json.loads(content)
            logging.info(f"Groq Response: {result}")
            return result
        except Exception as e:
            logging.error(f"Groq Error: {e}")
            return {
                "decision": "FOLLOW",
                "reason": "AI Analyst unavailable, falling back to algorithm.",
                "est_profit": "Calc by System",
                "est_loss": "Calc by System",
                "risk_score": 5,
            }

    async def ai_fix_code(self, code_content, error_message):
        """
        Mengirim kode rusak ke AI untuk diperbaiki syntax-nya (versi async).
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
            completion = await self.client.chat.completions.create(
                model="meta-llama/llama-guard-4-12b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.1,
            )
            fixed_code = completion.choices[0].message.content
            if fixed_code is None:
                return None
            fixed_code = fixed_code.replace("```python", "").replace("```", "").strip()
            return fixed_code
        except Exception as e:
            logging.error(f"AI Fix Code Error: {e}")
            return None
