import json  

def convert_to_requests(input_file, output_file):  
    # 读取输入JSON文件  
    with open(input_file, 'r', encoding='utf-8') as f:  
        data = json.load(f)  
    
    # 转换每个测试用例  
    with open(output_file, 'w', encoding='utf-8') as f:  
        for item in data:  
            if len(item['test_prompt']) > 8192:
                print(f"测试用例 {item['test_id']} 的长度超过了8192字符，已被忽略！")
                continue
            # 第一种格式的请求  
            request = {  
                "custom_id": f"test-{item['test_id']}",  
                "body": {  
                    "messages": [  
                        {  
                            "role": "user",  
                            "content": item['test_prompt']  
                        }  
                    ],  
                    "max_tokens": 8192,  
                    "top_p": 1  
                }
            }  
            
            f.write(json.dumps(request, ensure_ascii=False) + '\n')  
    
    print(f"转换完成！输出文件：{output_file}")  

if __name__ == "__main__":  
    convert_to_requests('../testdata_V3/test_v3_4-2.json', '../Output_jsonl_V3/code_analysis_requests_v3_4-2.jsonl')