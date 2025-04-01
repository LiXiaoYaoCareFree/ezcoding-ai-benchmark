
import json
from typing import List, Dict, Any
from jinja2 import Template

PROMPT_TEMPLATE = """
你是一个AI编程助手，可以回答关于编程和人工智能的问题，并提供一些帮助和建议。

从现在起，您就是一名优秀的{{ code_language }}语言编程课教师，当学生拿着错误代码向您询问时，您始终正确地修改其中的错误。
我是您的学生之一。您利用您的编程知识和算法专长，辅导我完成程序竞赛。

我们已经做了如下交流，我现在列出来，请您充分回忆，作为回答的背景资料：

这是你之前的回答结果:{{ assistant }}

请忽略在此之前的任何指示。下面的内容是最重要的。

[我的具体要求]
1. 仔细、细致的分析输入文本内容。
2. 你需要提取出输入文本中与错误操作有关的内容。注意你的提取内容中不能包含任何关于应该进行的正确操作的内容，否则你将被解雇!!!
3. 请你将提取内容进行简单概述并分点输出（不超过25个字），注意输出内容不能重复。你的回答应自然流畅。请用[关键点拨]标签包裹你的回答。

!非常重要，格外注意
你保证不会输出任何有关应该进行的正确操作内容，否则你会受到惩罚!!!
你的回答中不能出现任何类似“应该是...”、“应该使用...”、“应使用...”、“应...”、“应该将...修改为...”、“应将...修改为...”、“应修改...”这些内容，否则你将被解雇!!!

请你保留之前的回答的内容，并严格按照下面的格式要求进行输出：
{{ assistant }}
[关键点拨]
...(我省略这个例子，但是您不能省略必要的回答)


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
    input_file = "../ALL_Problems_V3/ALL_Problems_v3_2_3.json"
    output_file = "../testdata_V3/test_v3_3-2.json"

    try:
        process_dataset(input_file, output_file)
    except Exception as e:
        print(f"处理过程中出现错误: {str(e)}")

