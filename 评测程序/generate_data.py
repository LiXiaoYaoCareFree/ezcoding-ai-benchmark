import json
from typing import List, Dict, Any
from jinja2 import Template

# 定义提示词模板
PROMPT_TEMPLATE = """
题目描述:
{{content}}
以下是一段包含错误的{{ code_language }}语言代码，请帮助修复它:
```c
{{buggy_code}}
```
请提供修复后的完整代码。注意:
1. 代码必须能够正确处理所有测试用例
2. 保持代码结构清晰，添加必要的注释
3. 确保输入输出格式与题目要求一致
注意：最终的正确代码用markdown标签
```c 
```
包裹！
"""

def process_dataset(input_file: str, output_file: str):
    # 读取原始数据
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    test_cases: List[Dict[str, Any]] = []
    test_id = 1
    
    # 处理每个题目
    for problem in data:
        # 检查是否有测试用例
        if not problem.get('test_case'):
            continue
            
        problem_content = problem['content']
        test_cases_data = problem['test_case']
        
        # 处理每个错误提交
        for submission in problem['submissions']:
            buggy_code = submission['buggy_code']
            
            # 使用模板生成提示词
            template = Template(PROMPT_TEMPLATE)
            prompt = template.render(
                content=problem_content,
                buggy_code=buggy_code,
                code_language="C"
            )
            
            # 创建测试用例对象
            test_case = {
                'test_id': test_id,
                'test_case': test_cases_data,
                'test_prompt': prompt
            }
            
            test_cases.append(test_case)
            test_id += 1
    
    # 保存处理后的数据
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(test_cases, f, ensure_ascii=False, indent=2)
    
    print(f"处理完成! 共生成 {len(test_cases)} 个测试用例")

if __name__ == "__main__":
    # 使用示例
    input_file = "../dataset/ALL_Problems_250216.json"  # 原始数据文件路径
    output_file = "../testdata_V3/test_v3_0.json"  # 输出文件路径
    
    try:
        process_dataset(input_file, output_file)
    except Exception as e:
        print(f"处理过程中出现错误: {str(e)}")
