import json  
import tiktoken  
import numpy as np  
from tqdm import tqdm  

def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613"):  
    """计算消息列表中的token数量"""  
    encoding = tiktoken.encoding_for_model(model)  
    tokens_per_message = 3  # 每条消息的基础token数  
    tokens_per_name = 1     # 每个名字的基础token数  
    
    num_tokens = 0  
    for message in messages:  
        num_tokens += tokens_per_message  
        for key, value in message.items():  
            num_tokens += len(encoding.encode(str(value)))  
            if key == "name":  
                num_tokens += tokens_per_name  
    num_tokens += 3  # 每个回复的基础token数  
    return num_tokens  

def estimate_tokens_for_dataset(input_file):  
    """估算整个数据集的token使用量"""  
    # 读取输入JSON文件  
    with open(input_file, 'r', encoding='utf-8') as f:  
        data = json.load(f)  
    
    # 用于存储统计信息  
    token_counts = []  
    total_tokens = 0  
    request_counts = 0  
    
    print("正在估算token数量...")  
    for item in tqdm(data):  
        # 估算第一种请求格式的token数  
        messages1 = [  
            {"role": "user", "content": item['test_prompt']}  
        ]  
        tokens1 = num_tokens_from_messages(messages1)  
        
        token_counts.extend([tokens1])  
        total_tokens += tokens1
        request_counts += 1
    
    # 计算统计信息  
    avg_tokens = np.mean(token_counts)  
    std_tokens = np.std(token_counts)  
    min_tokens = np.min(token_counts)  
    max_tokens = np.max(token_counts)  
    
    # 计算成本估算（使用DeepSeek-R1的价格）  
    cost_per_1k_tokens = 0.002  # 0.002 ￥ per 1K tokens  
    estimated_cost = (total_tokens / 1000) * cost_per_1k_tokens  
    
    print("\n=== Token 使用估算报告 ===")  
    print(f"总发送请求数: {request_counts}")  
    print(f"总发送 token 数: {total_tokens:,}")  
    print(f"平均每个发送请求 token 数: {avg_tokens:.2f}")  
    print(f"发送 token 数标准差: {std_tokens:.2f}")  
    print(f"最小发送 token 数: {min_tokens}")  
    print(f"最大发送 token 数: {max_tokens}")  
    print(f"\n估计总成本（发送+推理+响应）: ￥{4 * estimated_cost:.2f}") 
    return total_tokens, stats  

if __name__ == "__main__":  
    # pip install tiktoken numpy tqdm  
    total_tokens, stats = estimate_tokens_for_dataset('test_data.json')