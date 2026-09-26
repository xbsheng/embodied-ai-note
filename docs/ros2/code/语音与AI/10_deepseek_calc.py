# Please install OpenAI SDK first: `pip3 install openai`
import os
from openai import OpenAI

# 初始化客户端
client = OpenAI(
    api_key='sk-a80719c8b9cc4c708195d7f84fdd4a70',
    base_url="https://api.deepseek.com"
)

# 发送请求
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "100 + 333 等于多少"},
    ],
    stream=False
)

# 打印结果
print(response.choices[0].message.content)
