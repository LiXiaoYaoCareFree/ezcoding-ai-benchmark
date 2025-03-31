import json
from typing import List, Dict, Any
from jinja2 import Template

# 定义提示词模板
PROMPT_TEMPLATE = """
题目描述:
{{content}}
[你的身份]您是一位优秀的AI编程课教师助手，有着对于{{ code_language }}的专业背景知识和丰富教学经验。
从现在起，我是您的学生之一，当我拿着代码向您询问时，请您认真理解题目要求，始终正确地引导我进行思考。
 
[你要做什么]
接下来，我会给您一段{{ code_language }}语言的代码，请您仔细阅读并做到有理有据严格遵循我给出的所有指示。
请您指出这段代码的意图和代码编写思路是什么，分段回答，抓住重点，不管细枝末节，内容简练扼要。
无论代码对错，您都只关心分析代码呈现出的意图。用[宏观解读]标签包裹您的回答。

!非常重要，格外注意
需要格外注意的是：您不关心代码中可能存在的问题与错误，您只进行思路上的解读！

以下是代码:
{{ buggy_code }}
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
    output_file = "../testdata/test_data.json"  # 输出文件路径

    try:
        process_dataset(input_file, output_file)
    except Exception as e:
        print(f"处理过程中出现错误: {str(e)}")
