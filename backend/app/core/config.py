import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME = os.getenv("APP_NAME", "LexFlow")
    APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

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