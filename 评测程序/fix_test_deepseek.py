import json  
from datetime import datetime  
from typing import Dict, List  
from rich.console import Console  
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn  

console = Console()  

class CheckpointFixer:  
    def __init__(self,   
                 test_data_file: str,  
                 checkpoint_file: str,  
                 response_file: str,  
                 output_file: str = None):  
        self.test_data_file = test_data_file  
        self.checkpoint_file = checkpoint_file  
        self.response_file = response_file  
        self.output_file = output_file or f"fixed_{checkpoint_file}"  
        
        self.test_data = self._load_json(test_data_file)  
        self.checkpoint = self._load_json(checkpoint_file)  
        self.responses = self._load_response_data()  
        
    def _load_json(self, file_path: str) -> Dict:  
        with open(file_path, 'r', encoding='utf-8') as f:  
            return json.load(f)  
            
    def _load_response_data(self) -> Dict[int, str]:  
        """加载响应文件"""  
        responses = {}  
        try:  
            with open(self.response_file, 'r', encoding='utf-8') as f:  
                for line in f:  
                    record = json.loads(line)  
                    if record["error"] is None:  
                        test_id = int(record["custom_id"].split("-")[-1])  
                        content = record["response"]["body"]["choices"][0]["message"]["content"]  
                        responses[test_id] = content  
        except Exception as e:  
            console.print(f"[red]加载响应文件失败: {str(e)}[/red]")  
            raise  
        return responses  

    def _create_error_entry(self, test_id: int, test_case: Dict, response: str) -> Dict:  
        """创建错误记录条目"""  
        return {  
            'timestamp': datetime.now().isoformat(),  
            'passed': False,  
            'message': "代码提取失败",  
            'code': None,  
            'response': response,  
            'model': "DeepSeek-R1-Qwen-32B",  # 根据实际情况修改  
            'prompt': test_case['test_prompt'],  
            'test_case': test_case['test_case']  
        }  

    def fix_checkpoint(self):  
        console.print("[bold green]开始修复checkpoint文件...[/bold green]")  
        
        missing_count = 0  
        fixed_checkpoint = self.checkpoint.copy()  
        
        with Progress(  
            SpinnerColumn(),  
            TextColumn("[progress.description]{task.description}"),  
            BarColumn(),  
            console=console  
        ) as progress:  
            task = progress.add_task("[cyan]检查缺失的测试点...", total=len(self.test_data))  
            
            for test_case in self.test_data:  
                test_id = str(test_case['test_id'])  
                progress.update(task, advance=1)  
                
                # 如果测试点不在checkpoint中  
                if test_id not in fixed_checkpoint:  
                    # 检查是否有对应的响应  
                    if int(test_id) in self.responses:  
                        response = self.responses[int(test_id)]  
                        # 创建错误记录  
                        fixed_checkpoint[test_id] = self._create_error_entry(  
                            int(test_id),  
                            test_case,  
                            response  
                        )  
                        missing_count += 1  
        
        # 保存修复后的checkpoint  
        with open(self.output_file, 'w', encoding='utf-8') as f:  
            json.dump(fixed_checkpoint, f, ensure_ascii=False, indent=2)  
        
        console.print(f"[bold green]修复完成！[/bold green]")  
        console.print(f"添加了 [bold cyan]{missing_count}[/bold cyan] 个缺失的测试点")  
        console.print(f"修复后的文件已保存至: [bold]{self.output_file}[/bold]")  

def main():  
    fixer = CheckpointFixer(  
        test_data_file="../testdata/test_data.json",
        checkpoint_file="../checkpoint/Result_DeepSeek_v3_5.json",
        response_file="../testdata_jsonl/results_v3_0.jsonl"
    )  
    
    try:  
        fixer.fix_checkpoint()  
    except Exception as e:  
        console.print(f"[red]修复过程中出现错误: {str(e)}[/red]")  

if __name__ == "__main__":  
    main()