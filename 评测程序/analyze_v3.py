import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track
from rich.columns import Columns
from collections import Counter
import re
from rich.style import Style
from rich.text import Text

console = Console()


def load_and_analyze_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_tests = len(data)
    passed_tests = sum(1 for item in data.values() if item['passed'])
    failed_tests = total_tests - passed_tests

    models = set(item['model'] for item in data.values())

    failure_reasons = []
    for item in data.values():
        if not item['passed']:
            if "Runtime Error" in item['message']:
                failure_reasons.append("运行时错误")
            elif "Wrong Answer" in item['message']:
                failure_reasons.append("答案错误")
            else:
                failure_reasons.append("其他错误")

    failure_counts = Counter(failure_reasons)

    return {
        'total': total_tests,
        'passed': passed_tests,
        'failed': failed_tests,
        'failure_counts': failure_counts,
        'models': list(models)
    }


def create_comparison_table(all_stats):
    table = Table(
        title="模型对比分析",
        title_style="bold magenta",
        border_style="blue",
        show_header=True,
        header_style="bold cyan"
    )

    table.add_column("评测指标", style="cyan")

    model_names = {
        "fixed_Result_DeepSeek_R1_671B": "DeepSeek-R1-671B",
        "fixed_checkpoint_DeepSeek_V3": "DeepSeek-V3",
        "Result_Spark_4.0_Ultra": "Spark-4.0-Ultra",
        "fixed_checkpoint_DeepSeek_R1_Qwen_32B": "DeepSeek-R1-Qwen-32B",
    }

    for model_file in all_stats.keys():
        model_name = model_names.get(model_file.replace("-fix.json", ""), model_file)
        table.add_column(model_name, style="magenta", justify="center")

    row_values = ["总测试数"]
    for stats in all_stats.values():
        row_values.append(str(stats['total']))
    table.add_row(*row_values, style="bold white")

    row_values = ["测试通过率"]
    for stats in all_stats.values():
        percentage = (stats['passed'] / stats['total'] * 100)
        row_values.append(f"{percentage:.2f}%")
    table.add_row(*row_values, style="bold green")

    error_types = ["运行时错误", "答案错误", "其他错误"]
    error_styles = {"运行时错误": "yellow", "答案错误": "red", "其他错误": "magenta"}

    for error_type in error_types:
        row_values = [error_type]
        for stats in all_stats.values():
            count = stats['failure_counts'].get(error_type, 0)
            percentage = (count / stats['total'] * 100)
            row_values.append(f"{percentage:.2f}%")
        table.add_row(*row_values, style=f"bold {error_styles[error_type]}")

    return table


def create_result_visualization(stats, model_name, width=120):
    total = stats['total']
    passed = stats['passed']
    pass_percentage = (passed / total * 100)

    error_percentages = []
    colors = {"运行时错误": "yellow", "答案错误": "red", "其他错误": "magenta"}

    for error_type, count in stats['failure_counts'].items():
        percentage = (count / total * 100)
        error_percentages.append((error_type, percentage))

    bar_segments = []
    current_pos = 0

    passed_width = int(width * pass_percentage / 100)
    bar_segments.append(f"[green]{'█' * passed_width}[/green]")
    current_pos += passed_width

    for error_type, percentage in error_percentages:
        error_width = int(width * percentage / 100)
        bar_segments.append(f"[{colors[error_type]}]{'█' * error_width}[/{colors[error_type]}]")
        current_pos += error_width

    if current_pos < width:
        bar_segments[
            -1] += f"[{colors[error_percentages[-1][0]]}]{'█' * (width - current_pos)}[/{colors[error_percentages[-1][0]]}]"

    return Panel(
        f"{''.join(bar_segments)}",
        title=f"{model_name} 测试结果分布",
        border_style="green",
        padding=(1, 2)
    )


def create_task_info_panel():
    task_info = """[bold]测试任务:[/bold] 代码纠错 + OJ评审  
[bold]数据集:[/bold] ITSP + 北邮YBK"""
    return Panel(
        task_info,
        title="任务信息",
        border_style="cyan",
        padding=(1, 2)
    )


def main():
    console_width = console.width
    title = Text("LLM多模型对比分析报告", style="bold blue")
    title.align("center", console_width)
    console.print("\n")
    console.print(Panel(title, border_style="blue", padding=(1, 20)))
    console.print("\n")

    try:
        model_files = [
            "fixed_Result_DeepSeek_R1_671B-fix.json",
            "fixed_checkpoint_DeepSeek_V3-fix.json",
            "Result_Spark_4.0_Ultra-fix.json",
            "fixed_checkpoint_DeepSeek_R1_Qwen_32B-fix.json",
        ]

        all_stats = {}
        for file in model_files:
            all_stats[file] = load_and_analyze_data(file)

        console.print(create_task_info_panel())
        console.print("")

        console.print(create_comparison_table(all_stats))
        console.print("")

        model_names = {
            "fixed_Result_DeepSeek_R1_671B-fix.json": "DeepSeek-R1-671B",
            "fixed_checkpoint_DeepSeek_V3-fix.json": "DeepSeek-V3",
            "Result_Spark_4.0_Ultra-fix.json": "Spark-4.0-Ultra",
            "fixed_checkpoint_DeepSeek_R1_Qwen_32B-fix.json": "DeepSeek-R1-Qwen-32B",
        }

        for file, stats in all_stats.items():
            model_name = model_names[file]
            console.print(create_result_visualization(stats, model_name))
            console.print("")

    except FileNotFoundError:
        console.print("[red]错误: 未找到指定的JSON文件![/red]")
    except Exception as e:
        console.print(f"[red]发生错误: {str(e)}[/red]")


if __name__ == "__main__":
    main()