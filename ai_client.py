"""共享的 OpenAI 兼容客户端，供各蓝图使用。"""
import os

import openai
from dotenv import load_dotenv

load_dotenv()

client = openai.OpenAI(
    api_key=os.getenv("PARATERA_API_KEY"),
    base_url="https://llmapi.paratera.com/v1/",
)
