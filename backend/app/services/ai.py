import os

from openai import OpenAI


client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


class AIService:

    def summarize_document(
        self,
        text: str,
    ) -> str:

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a legal assistant. "
                        "Summarize legal documents in concise bullet points."
                    ),
                },
                {
                    "role": "user",
                    "content": text,
                },
            ],
        )

        return response.choices[0].message.content


ai_service = AIService()