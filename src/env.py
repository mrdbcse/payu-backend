import os

from dotenv import load_dotenv

load_dotenv()

ENV = "LIVE"


def config(env: str = ENV) -> dict:
    return {
        "key": os.getenv(f"{env}_MERCHANT_KEY"),
        "salt": os.getenv(f"{env}_MERCHANT_SALT"),
        "action_url": os.getenv(f"{env}_ACTION_URL"),
        "payu_url": os.getenv(f"{env}_PAYU_URL"),
    }
