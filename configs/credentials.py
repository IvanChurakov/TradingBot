import os
from dotenv import load_dotenv

load_dotenv()

class Credentials:
    def __init__(self):
        self.api_key = os.getenv("API_KEY")
        self.api_secret = os.getenv("API_SECRET")