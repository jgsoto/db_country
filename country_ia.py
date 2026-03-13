import os
import re
import pycountry
from openai import OpenAI


class IAGroqPais:

    def __init__(self):
        self.api_key = os.environ.get("GROQCLOUD_API_KEY")
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.groq.com/openai/v1",
        )

    def obtener_iso3_ia(self, location):

        prompt = f"""
        Infer the country from this social media location.
        Use cities, regions, or abbreviations if present.
        If impossible return NONE.

        Return ONLY the ISO3 code.

        Location: "{location}"
        """

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=4,
            )

            resultado = response.choices[0].message.content.strip().upper()

            match = re.search(r"\b[A-Z]{3}\b", resultado)

            if match and pycountry.countries.get(alpha_3=match.group(0)):
                return match.group(0)

            if "NONE" in resultado:
                return None

        except Exception as e:
            print("Error IA:", e)

        return None