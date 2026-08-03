from dotenv import load_dotenv
import os

load_dotenv()


class Settings:
    APP_NAME = os.getenv("APP_NAME", "LexFlow")
    APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://localhost/lexflow"
    )

    SECRET_KEY = os.getenv("SECRET_KEY", "")


settings = Settings()