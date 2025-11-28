# # Please install OpenAI SDK first: `pip3 install openai`
# import os
# from openai import OpenAI

# api_key = 'sk-99ed7f2e56bd478cb3147fd1593d4157'
# client = OpenAI(
#     api_key=api_key,
#     base_url="https://api.deepseek.com")

# response = client.chat.completions.create(
#     model="deepseek-chat",
#     messages=[
#         {"role": "system", "content": "You are a helpful assistant"},
#         {"role": "user", "content": "Hello"},
#     ],
#     stream=False
# )

# print(response.choices[0].message.content)


import requests

GITHUB_TOKEN = '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'  # 替换为你的 GitHub Token
headers = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

url = f'https://api.github.com/repos/lvgl/lvgl'

response = requests.get(url, headers=headers)

print(response)