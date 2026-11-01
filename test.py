import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CREDENTIALS_FILE = Path(os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials(2).json")).expanduser().resolve()
TOKEN_FILE = Path(os.getenv("GOOGLE_TOKEN_FILE", "token.json")).expanduser().resolve()

print("Credentials file :", CREDENTIALS_FILE)
print("Credentials exists :", CREDENTIALS_FILE.is_file())

print("Token file :", TOKEN_FILE)
print("Token exists :", TOKEN_FILE.is_file())

