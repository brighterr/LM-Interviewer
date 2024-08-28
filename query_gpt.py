from openai import AzureOpenAI

from config import Config


key = Config.gpt_key
endpoint = Config.gpt_endpoint

model = "gpt-4-1106"
max_tokens = 4096


def query(msgs):
    llm = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=key,
        api_version="2023-12-01-preview",
    )

    response = llm.chat.completions.create(
        model=model,
        messages=msgs,
        max_tokens=max_tokens,
    )
    response = response.choices[0].message.content
    # print(response)
    return response


def add_user_msg(msgs, msg):
    msgs.append({'role': 'user', 'content': msg})
    

def add_model_msg(msgs, msg):
    msgs.append({'role': 'assistant', 'content': msg})


def main():
    print(query([{
        'role': 'user',
        'content': '你好！'
    }]))


if __name__ == '__main__':
    main()

