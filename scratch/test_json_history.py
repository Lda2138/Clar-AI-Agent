import os
import sys

from openai import OpenAI
from dotenv import load_dotenv
import json

env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

api_key = os.getenv("DEEPSEEK_API_KEY")
client = OpenAI(api_key=api_key, base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))

messages = [
    {"role": "system", "content": "请按照 JSON 格式返回，包含 'reply' 字段。"},
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！有什么我可以帮你的？"},
    {"role": "user", "content": "我想学习随机信号分析。"}
]

kwargs = {"model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"), "messages": messages, "temperature": 0.5, "max_tokens": 512}
kwargs["response_format"] = {"type": "json_object"}

response = client.chat.completions.create(**kwargs)
print(response.choices[0].message.content)
