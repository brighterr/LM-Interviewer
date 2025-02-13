import requests
from config import Config

# 你的 API 配置
url = "http://10.77.110.129:8000/v1/chat/completions"
headers = {
    "Content-Type": "application/json"
}

# 模型配置
model = "/home/zhangyuheng/.cache/modelscope/hub/Qwen/Qwen2.5-7B-Instruct"
max_tokens = 512

def query(msgs):
    # 构造请求数据
    data = {
        "model": model,
        "messages": msgs,
        "temperature": 0.7,
        "top_p": 0.8,
        "repetition_penalty": 1.05,
        "max_tokens": max_tokens,
    }

    # 发送请求
    response = requests.post(url, headers=headers, json=data)

    # 检查响应状态
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise Exception(f"API 请求失败: {response.status_code}, {response.text}")

def add_user_msg(msgs, msg):
    msgs.append({'role': 'user', 'content': msg})

def add_model_msg(msgs, msg):
    msgs.append({'role': 'assistant', 'content': msg})

def main():
    # 测试 query 函数
    print(query([{
        'role': 'user',
        'content': '你好！'
    }]))

if __name__ == '__main__':
    main()