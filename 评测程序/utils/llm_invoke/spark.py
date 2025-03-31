import hashlib  
import hmac  
import json  
import time  
import random  
from enum import Enum  
from typing import Optional, Dict  
import requests  

class ModelType(Enum):  
    SPARK4 = "SPARK-4"  
    SPARK3_5_GRAY = "SPARK-3.5-GRAY"
    GPT3_5 = "GPT-3.5"  
    GPT4 = "GPT-4"  

MODEL_CONFIG = {  
    ModelType.SPARK4: {  
        "endpoint": "/iflytek-websocket-openapi",  
        "domain": "4.0Ultra",  
    },  
    ModelType.SPARK3_5_GRAY: {  
        "endpoint": "/iflytek-websocket-openapi-beta",  
        "domain": "generalv3.5tigray",  
    },  
    ModelType.GPT3_5: {  
        "endpoint": "/chatgpt",  
        "model": "gpt-3.5-turbo",  
    },  
    ModelType.GPT4: {  
        "endpoint": "/chatgpt",  
        "model": "gpt-4-turbo-preview",  
    },  
}  

config = {  
        "eb_app_id": "ziov8sUuW179aji4",
        "eb_api_key": "FggDstRfsCAwEAAQJAE6b7zVSQ",
        "eb_api_url": "http://10.91.129.95:8080",
    }  

def get_ebyte_response(  
    prompt: str,  
    config: Dict = config,  
    model_type: ModelType = ModelType.SPARK4,  
    temperature: float = 0.5,  
    timeout: int = 30  
) -> str:  
    """  
    同步获取大模型响应  
    
    :param prompt: 用户输入的提示词  
    :param config: 包含认证信息的配置字典  
        {  
            "eb_app_id": "your_app_id",  
            "eb_api_key": "your_api_key",  
            "eb_api_url": "http://api.example.com"  
        }  
    :param model_type: 模型类型枚举值  
    :param temperature: 温度参数，默认0.5  
    :param timeout: 请求超时时间，默认30秒  
    :return: 完整的模型响应文本  
    """  
    # 获取模型配置  
    model_config = MODEL_CONFIG[model_type]  
    
    # 生成请求参数  
    timestamp = str(int(time.time() * 1000))  
    nonce = str(random.randint(0, 1000000))  
    
    # 构造基础headers  
    headers = {  
        "X-EBAPI-Timestamp": timestamp,  
        "X-EBAPI-Nounce": nonce,  
    } 

    # 构造请求体  
    if model_type in [ModelType.SPARK4, ModelType.SPARK3_5_GRAY]:  
        payload = {  
            "header": {},  
            "parameter": {  
                "chat": {  
                    "domain": model_config["domain"],  
                    "temperature": temperature,  
                    "max_tokens": 8192  
                }  
            },  
            "payload": {  
                "message": {  
                    "text": [{  
                        "role": "user",  
                        "content": prompt  
                    }]  
                }  
            }  
        }  
    else:  # GPT 系列  
        payload = {  
            "model": model_config["model"],  
            "messages": [{  
                "role": "system",  
                "content": f"You are ChatGPT, a large language model trained by OpenAI. Current model: {model_config['model']}"  
            }, {  
                "role": "user",  
                "content": prompt  
            }],  
            "temperature": temperature,  
            "stream": True  
        }  

    # 生成签名  
    json_data = json.dumps(payload).encode('utf-8')  
    hashed_data = hashlib.md5(json_data).hexdigest().upper()  
    ordered_params = sorted(headers.items(), key=lambda x: x[0])  

    ordered_str = ";".join(f"{k.lower()}={v}" for k, v in ordered_params)  

    signature_str = (  
        f"POST:{model_config['endpoint']}:application/json:{ordered_str}:{hashed_data}::{timestamp}:{nonce}"  
    )  

    signature = hmac.new(  
        config["eb_api_key"].encode(),  
        signature_str.encode(),  
        hashlib.sha256  
    ).hexdigest()  

    # 添加认证头  
    headers.update({  
        "Authorization": f"EBAPI {config['eb_app_id']}:{signature}",  
        "Content-Type": "application/json",
        "Accept" : "text/event-stream"
    })  

    # 发送请求  
    response = requests.post(  
        config["eb_api_url"] + model_config["endpoint"],  
        headers=headers,  
        json=payload,  
        stream=True,  
        timeout=timeout  
    )  

    if response.status_code != 200:  
        raise Exception(f"API请求失败: {response.text}")  

    # 处理流式响应  
    full_response = ""  
    for line in response.iter_lines():  
        if not line:  
            continue  
            
        data = line.decode("utf-8").lstrip("data: ")  
        if data == "[DONE]":  
            break  

        try:  
            json_data = json.loads(data)  
        except json.JSONDecodeError:  
            continue  

        # 处理不同模型的响应格式  
        if model_type in [ModelType.SPARK4, ModelType.SPARK3_5_GRAY]:  
            # 处理星火异常  
            if json_data.get("header", {}).get("code") in (10013, 10014):  
                return "非常抱歉，根据相关法律法规，我们无法提供关于此问题的答案。"  
            content = json_data.get("payload", {}).get("choices", {}).get("text", [{}])[0].get("content")  
        else:  # GPT 系列  
            choices = json_data.get("choices", [])  
            if not choices:  
                continue  
            content = choices[0].get("delta", {}).get("content")  

        if content:  
            full_response += content  

    return full_response

if __name__ == "__main__":  
    
    print("----- standard request -----")
    response = get_ebyte_response(prompt="讲一个冷笑话")  
    print(response)
