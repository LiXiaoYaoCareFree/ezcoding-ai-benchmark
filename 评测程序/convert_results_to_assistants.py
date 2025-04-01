
import json

# 文件路径
results_path = "../Results_V3_1/results_v3_4.jsonl"
all_problems_path = "../评测数据集/ALL_Problems_250216.json"
output_path = "../ALL_Problems_V3/ALL_Problems_250216_v3_4.json"

# 读取 results.jsonl 中的每一行
with open(results_path, "r", encoding="utf-8") as f:
    results_lines = f.readlines()
    results = [json.loads(line) for line in results_lines]

# 构建 custom_id -> content 映射表
customid_to_content = {
    item["custom_id"]: item["response"]["body"]["choices"][0]["message"]["content"]
    for item in results
}

# 读取原始 ALL_Problems_250216.json
with open(all_problems_path, "r", encoding="utf-8") as f:
    all_problems = json.load(f)

# 遍历所有题目并添加 assistant 字段
for problem in all_problems:
    if "submissions" in problem:
        for submission in problem["submissions"]:
            if results:
                result = results.pop(0)  # 按顺序取出
                content = result["response"]["body"]["choices"][0]["message"]["content"]
                submission["assistant"] = content  # 添加 assistant 字段

# 写入更新后的文件
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(all_problems, f, ensure_ascii=False, indent=2)

print("转换完成，文件已保存为 ALL_Problems_250216_v3_4.json")
