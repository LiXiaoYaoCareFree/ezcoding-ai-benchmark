
import json
from typing import List, Dict, Any
from jinja2 import Template

# 定义提示词模板
PROMPT_TEMPLATE = """
你是一个AI编程助手，可以回答关于编程和人工智能的问题，并提供一些帮助和建议。

从现在起，您就是一名优秀的{{ code_language }}语言编程课教师，当学生拿着错误代码向您询问时，您始终正确地修改其中的错误。
我是您的学生之一。您利用您的编程知识和算法专长，辅导我完成程序竞赛。

我们已经做了如下交流，我现在列出来，请您充分回忆，作为回答的背景资料：

user:{请帮我进行代码的[宏观解读]}
这是你之前的回答结果:{{ assistant }}

请忽略在此之前的任何指示。下面的内容是最重要的。

[你的身份]您是一位优秀的代码分析师，有着对于{{ code_language }}的丰富编程经验，理解一切代码。
从现在起，我是您的学生之一，当我代码向您询问时，您始终正确地帮助我进行代码指导。

[你要做什么]
下面我将向你呈现我的要求和一段代码，请你按照如下的要求完成我的任务，请深呼吸一口，阅读并确保理解后，按我的要求进行回答。

[具体的任务]
1.代码分析：请您指出这段代码的意图和代码编写思路是什么。无论代码对错，您都只关心分析代码呈现出的意图。如果要求或代码中涉及到某项关键的库或模块、数据结构或算法，请注意在意图和思路中有所体现。请不仅关注函数整体的功能，也一定要注重展开叙述函数内代码的意图和思路。
2.代码注释：您需要正确理解输入代码，然后利用您专业的编程知识将输入代码进行详尽清晰的中文注释，输入代码中有英文注释时请翻译成中文。请您将最终的代码与中文注释一并输出。

这是今年最重要的问题，请发挥你所有的潜能来解决！！！

请您严格按照下面的格式要求进行输出：
[宏观解读]
user:请帮我进行代码宏观解读
这是你之前的回答结果:{{ assistant }}
[代码注释]
将细致准确的解读结果通过注释形式放在代码中输出。只输出这段代码不输出其他内容。

下面是您要处理的输入代码:
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
            assistant = submission['assistant']

            if not buggy_code or not assistant:
                continue

            # 使用模板生成提示词
            template = Template(PROMPT_TEMPLATE)
            prompt = template.render(
                content=problem_content,
                buggy_code=buggy_code,
                code_language="C",
                assistant=assistant,
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
    input_file = "../testdata_jsonl/ALL_Problems_250216_updated.json"  # 原始数据文件路径
    output_file = "../testdata/test_v3_2.json"  # 输出文件路径

    try:
        process_dataset(input_file, output_file)
    except Exception as e:
        print(f"处理过程中出现错误: {str(e)}")
