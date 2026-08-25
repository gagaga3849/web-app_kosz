import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///dev.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEFAULT_LOCALE = "pl"
    DEFAULT_REGION = "pl"
    DEFAULT_CURRENCY = "PLN"
    LABOR_HOURS_PER_DAY = 8
