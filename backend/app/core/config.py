import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME = os.getenv("APP_NAME", "LexFlow")
    APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    # Groq retires models over time, so the model is a setting rather than hard-coded.
    LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-20b")
    # Stay under the account's tokens-per-minute limit (8,000 on Groq's free tier).
    LLM_TOKENS_PER_MINUTE = int(os.getenv("LLM_TOKENS_PER_MINUTE", "8000"))
    # Long documents are read in sections of about this many characters (~4,000 tokens).
    LLM_SECTION_CHARS = int(os.getenv("LLM_SECTION_CHARS", "16000"))

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://localhost/lexflow"
    )

    SECRET_KEY = os.getenv("SECRET_KEY", "")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )


settings = Settings()
