import json
import logging
import os
import time
from typing import Dict, List, Optional
from datetime import datetime
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.table import Table
from rich import print as rprint
from utils.oj_runner.client import run_c_code_in_oj

console = Console()


def setup_logging(log_dir: str = "logs") -> None:
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"inference_ds2_{timestamp}.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            # RichHandler(rich_tracebacks=True, console=console)
        ]
    )


class ModelInferenceRunner:
    def __init__(self, test_data_file: str, response_file: str = "results.jsonl",
                 checkpoint_file: str = "checkpoint_ds.json"):
        self.test_data_file = test_data_file
        self.checkpoint_file = checkpoint_file
        self.log_dir = "logs"
        self.error_log_file = os.path.join(
            self.log_dir,
            f"error_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        self.test_data = self._load_test_data()
        self.completed_tests = self._load_checkpoint()
        self.statistics = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'error': 0
        }
        self.response_data = self._load_response_data(response_file)

    def _load_response_data(self, response_file: str) -> Dict[int, str]:
        """加载本地响应文件"""
        responses = {}
        try:
            with open(response_file, 'r', encoding='utf-8') as f:
                for line in f:
                    record = json.loads(line)
                    if record["error"] is None:
                        # 提取test_id：从custom_id中获取数字部分
                        test_id = int(record["custom_id"].split("-")[-1])
                        content = record["response"]["body"]["choices"][0]["message"]["content"]
                        responses[test_id] = content
        except Exception as e:
            logging.error(f"加载响应文件失败: {str(e)}")
            raise
        return responses

    def _load_test_data(self) -> List[Dict]:
        with open(self.test_data_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_checkpoint(self) -> Dict[int, Dict]:
        if os.path.exists(self.checkpoint_file):
            with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_checkpoint(self) -> None:
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(self.completed_tests, f, ensure_ascii=False, indent=2)

    def _extract_code_from_response(self, response: str) -> Optional[str]:
        try:
            start_marker = "```c"
            end_marker = "```"

            start_idx = response.find(start_marker)
            if start_idx == -1:
                return None

            start_idx = response.find("\n", start_idx) + 1
            end_idx = response.find(end_marker, start_idx)

            if end_idx == -1:
                return None

            return response[start_idx:end_idx].strip()
        except Exception as e:
            logging.error(f"代码提取失败: {str(e)}")
            return None

    def _log_detailed_error(self, test_id: int, error_type: str, error_msg: str,
                            context: Dict = None, exception: Exception = None) -> None:
        """
        详细记录错误信息到日志

        Args:
            test_id: 测试用例ID
            error_type: 错误类型
            error_msg: 错误信息
            context: 相关上下文数据
            exception: 异常对象
        """
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "test_id": test_id,
            "error_type": error_type,
            "error_message": error_msg,
            "context": context or {},
        }

        if exception:
            error_data.update({
                "exception_type": type(exception).__name__,
                "exception_msg": str(exception),
                "traceback": logging.traceback.format_exc()
            })

        logging.error(f"详细错误信息:\n{json.dumps(error_data, indent=2, ensure_ascii=False)}")

    def display_statistics(self):
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("总数", style="cyan")
        table.add_column("通过", style="green")
        table.add_column("失败", style="red")
        table.add_column("错误", style="yellow")
        table.add_column("通过率", style="cyan")

        pass_rate = (self.statistics['passed'] / self.statistics['total'] * 100) if self.statistics['total'] > 0 else 0

        table.add_row(
            str(self.statistics['total']),
            str(self.statistics['passed']),
            str(self.statistics['failed']),
            str(self.statistics['error']),
            f"{pass_rate:.2f}%"
        )

        console.print("\n[bold]测试统计[/bold]")
        console.print(table)

    def process_test_case(self, test_id: int, test_case: Dict, model: str, progress: Progress, task_id: int) -> None:
        """处理单个测试用例"""
        context = {
            "test_id": test_id,
            "model": model,
            "test_case": test_case
        }
        try:
            # 获取模型响应
            prompt = test_case['test_prompt']
            # 如果内容太长就跳过
            if len(prompt) > 8192:
                logging.info(f"跳过测试 {test_id}，提示词过长")
                return
            progress.update(task_id, description=f"[cyan]读取模型响应 (ID: {test_id})")
            if test_id not in self.response_data:
                self._log_detailed_error(
                    test_id,
                    "MISSING_RESPONSE",
                    "本地响应文件中找不到对应的测试ID",
                    context
                )
                raise ValueError(f"测试ID {test_id} 的响应不存在")

            response = self.response_data[test_id]
            context["model_response"] = response
            # 提取代码
            try:
                code = self._extract_code_from_response(response)
                if not code:
                    self._log_detailed_error(
                        test_id,
                        "CODE_EXTRACTION_ERROR",
                        "无法从响应中提取代码",
                        {**context, "response": response}
                    )
                    raise ValueError("无法从响应中提取代码")
                context["extracted_code"] = code
            except Exception as e:
                self._log_detailed_error(
                    test_id,
                    "CODE_EXTRACTION_ERROR",
                    "代码提取过程出错",
                    context,
                    e
                )
                raise

                # 运行测试
            progress.update(task_id, description=f"[cyan]运行测试 (ID: {test_id})")
            try:
                passed, message = run_c_code_in_oj(code, test_case['test_case'])
                context["test_result"] = {"passed": passed, "message": message}
            except Exception as e:
                self._log_detailed_error(
                    test_id,
                    "TEST_EXECUTION_ERROR",
                    "代码执行测试失败",
                    context,
                    e
                )
                raise

                # 更新统计
            self.statistics['total'] += 1
            if passed:
                self.statistics['passed'] += 1
                rprint(f"[green]✓ 测试 {test_id} 通过[/green]")
                logging.info(f"测试通过 - ID: {test_id}")
            else:
                self.statistics['failed'] += 1
                # rprint(f"[red]✗ 测试 {test_id} 失败: {message}[/red]")
                self._log_detailed_error(
                    test_id,
                    "TEST_FAILURE",
                    f"测试失败: {message}",
                    context
                )

                # 记录结果
            result = {
                'timestamp': datetime.now().isoformat(),
                'passed': passed,
                'message': message,
                'code': code,
                'response': response,
                'model': model,
                'prompt': prompt,
                'test_case': test_case['test_case']
            }

            self.completed_tests[str(test_id)] = result
            self._save_checkpoint()

        except Exception as e:
            self.statistics['error'] += 1
            self._log_detailed_error(
                test_id,
                "UNEXPECTED_ERROR",
                "处理测试用例时发生意外错误",
                context,
                e
            )

    def run_inference(self, start_id: int = 1, end_id: Optional[int] = None, model: str = "ark") -> None:
        # 确定要处理的测试用例范围
        test_cases = [tc for tc in self.test_data
                      if tc['test_id'] >= start_id and
                      (end_id is None or tc['test_id'] <= end_id)]

        # self.statistics['total'] = len(test_cases)
        self.statistics['total'] = 0

        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
                console=console
        ) as progress:

            task = progress.add_task(
                "[cyan]运行测试...",
                total=len(test_cases)
            )

            for test_case in test_cases:
                test_id = test_case['test_id']

                if str(test_id) in self.completed_tests:
                    progress.advance(task)
                    continue

                self.process_test_case(test_id, test_case, model, progress, task)
                progress.advance(task)
                time.sleep(1)

                # 完成后显示统计信息
            self.display_statistics()


def main():
    setup_logging()

    console.print(Panel.fit(
        "[bold green]代码测试系统[/bold green]\n"
        "支持断点续测和错误恢复",
        title="Welcome",
        border_style="blue"
    ))

    runner = ModelInferenceRunner(
        test_data_file="../testdata/test_data.json",
        response_file="../中间产物/VolcEngine_batch_response_DeepSeek_V3.jsonl",
        checkpoint_file="../checkpoint/checkpoint_DeepSeek_V3_raw.json")

    try:
        runner.run_inference(
            start_id=1,
            end_id=4682,
            model="DeepSeek-V3"
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]用户中断执行[/yellow]")
        runner.display_statistics()
    except Exception as e:
        console.print(f"\n[red]执行过程中出现错误: {str(e)}[/red]")
    finally:
        console.print("\n[bold green]测试任务结束[/bold green]")


if __name__ == "__main__":
    main()