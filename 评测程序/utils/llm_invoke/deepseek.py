from volcenginesdkarkruntime import Ark

client = Ark(
    # 您的方舟API Key
    api_key="", 
    # 深度推理模型耗费时间会较长，请您设置较大的超时时间，避免超时，推荐30分钟以上
    timeout=1800,
    )

def get_ark_response(prompt: str) -> str:
    completion = client.chat.completions.create(
        model="",
        messages=[
            {"role": "user", "content": prompt},
        ],
    )
    return completion.choices[0].message.content


if __name__ == "__main__":
    print("----- standard request -----")
    response = get_ark_response("你好")
    print(response)
    