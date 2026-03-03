import os
from dotenv import load_dotenv

load_dotenv()

okx_api_key = os.getenv("OKX_API_KEY")
okx_api_secret_key = os.getenv("OKX_API_SECRET_KEY")
okx_passphrase = os.getenv("OKX_PASSPHRASE")

flag = os.getenv("FLAG" , "1")
