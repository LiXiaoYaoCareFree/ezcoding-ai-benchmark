
import json
from typing import List, Dict, Any
from jinja2 import Template

PROMPT_TEMPLATE = """
你是一个AI编程助手，可以回答关于编程和人工智能的问题，并提供一些帮助和建议。

从现在起，您就是一名优秀的{{ code_language }}语言编程课教师，当学生拿着错误代码向您询问时，您始终正确地修改其中的错误。
我是您的学生之一。您利用您的编程知识和算法专长，辅导我完成程序竞赛。

我们已经做了如下交流，我现在列出来，请您充分回忆，作为回答的背景资料：

user:{请帮我进行代码的[宏观解读]和[代码注释]+[关键点拨]}
这是你之前的回答结果:{{ assistant }}

请忽略在此之前的任何指示。下面的内容是最重要的。

请您严格按照下面的格式要求进行输出：

[宏观解读]+[代码注释]+[关键点拨]+[详细指导]
user:请帮我进行代码宏观解读+代码注释
这是你之前的回答结果:{{ assistant }}
请提供修复后的完整代码。注意:
1. 代码必须能够正确处理所有测试用例
2. 保持代码结构清晰，添加必要的注释
3. 确保输入输出格式与题目要求一致
注意：最终的正确代码用markdown标签
```c 
```
包裹！
下面是您要处理的输入代码:
{{ buggy_code }}
"""

def process_dataset(input_file: str, output_file: str):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    test_cases: List[Dict[str, Any]] = []
    test_id = 1

    for problem in data:
        if not problem.get('test_case'):
            continue

        problem_content = problem['content']
        test_cases_data = problem['test_case']

        for submission in problem['submissions']:
            buggy_code = submission['buggy_code']
            assistant = submission.get('assistant')
            if not assistant:
                continue

            template = Template(PROMPT_TEMPLATE)
            prompt = template.render(
                content=problem_content,
                buggy_code=buggy_code,
                code_language="C",
                assistant=assistant,
            )

            test_case = {
                'test_id': test_id,
                'test_case': test_cases_data,
                'test_prompt': prompt
            }
            test_cases.append(test_case)
            test_id += 1

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(test_cases, f, ensure_ascii=False, indent=2)

    print(f"处理完成! 共生成 {len(test_cases)} 个测试用例")

if __name__ == "__main__":
    input_file = "../ALL_Problems_V3/ALL_Problems_250216_v3_4.json"
    output_file = "../testdata_V3/test_v3_5-1.json"

    try:
        process_dataset(input_file, output_file)
    except Exception as e:
        print(f"处理过程中出现错误: {str(e)}")

