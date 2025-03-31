import hashlib
import json

import requests

from .languages import c_lang_config, cpp_lang_config, java_lang_config, c_lang_spj_config, c_lang_spj_compile, py2_lang_config, py3_lang_config, go_lang_config, php_lang_config, js_lang_config
from .config import JUDGE_SERVER_TOKEN, JUDGE_SERVER_URL

class JudgeServerClientError(Exception):
    pass


class JudgeServerClient(object):
    def __init__(self, token, server_base_url):
        self.token = hashlib.sha256(token.encode("utf-8")).hexdigest()
        self.server_base_url = server_base_url.rstrip("/")

    def _request(self, url, data=None):
        kwargs = {"headers": {"X-Judge-Server-Token": self.token,
                              "Content-Type": "application/json"}}
        if data:
            kwargs["data"] = json.dumps(data)
        try:
            return requests.post(url, **kwargs).json()
        except Exception as e:
            raise JudgeServerClientError(str(e))

    def ping(self):
        return self._request(self.server_base_url + "/ping")

    def judge(self, src, language_config, max_cpu_time, max_memory, test_case_id=None, test_case=None, spj_version=None, spj_config=None,
              spj_compile_config=None, spj_src=None, output=False):
        if not (test_case or test_case_id) or (test_case and test_case_id):
            raise ValueError("invalid parameter")

        data = {"language_config": language_config,
                "src": src,
                "max_cpu_time": max_cpu_time,
                "max_memory": max_memory,
                "test_case_id": test_case_id,
                "test_case": test_case,
                "spj_version": spj_version,
                "spj_config": spj_config,
                "spj_compile_config": spj_compile_config,
                "spj_src": spj_src,
                "output": output}
        return self._request(self.server_base_url + "/judge", data=data)

    def compile_spj(self, src, spj_version, spj_compile_config):
        data = {"src": src, "spj_version": spj_version,
                "spj_compile_config": spj_compile_config}
        return self._request(self.server_base_url + "/compile_spj", data=data)
def run_c_code_in_oj(code, test_cases):  
    """  
    运行C代码并进行在线评测  
    
    Args:  
        code (str): C语言代码，换行使用\n  
        test_cases (list): 测试用例列表，每个测试用例是包含input和output的字典  
        
    Returns:  
        tuple: (是否通过, 错误信息)  
    """  
    # 服务器配置  
    token = JUDGE_SERVER_TOKEN
    server_base_url = JUDGE_SERVER_URL
    
    try:  
        # 创建客户端  
        client = JudgeServerClient(token=token, server_base_url=server_base_url)  
        
        # 检查服务器连接  
        try:  
            ping_result = client.ping()  
            if ping_result is None:  
                return False, f"Unable to connect to judge server at {server_base_url}"  
        except JudgeServerClientError:  
            return False, f"Failed to connect to judge server at {server_base_url}. Please check if the server is running and accessible."  
        except requests.exceptions.ConnectionError:  
            return False, "Connection error: Failed to connect to judge server. Please check server address and network connection."  
            
        # 提交代码进行评测  
        try:  
            result = client.judge(  
                src=code,  
                language_config=c_lang_config,  
                max_cpu_time=1000,  
                max_memory=1024 * 1024 * 128,  
                test_case=test_cases,  
                output=True  
            )  
        except JudgeServerClientError as e:  
            return False, f"Judge server error while submitting code: {str(e)}"  
        
        # 检查结果格式  
        if not isinstance(result, dict):  
            return False, f"Invalid response from judge server: {result}"  
            
        # 检查是否有编译错误  
        if result.get("err") == "CompileError":  
            return False, f"Compilation Error:\n{result.get('data', 'No error details available')}"  
            
        # 检查其他错误  
        if result.get("err"):  
            return False, f"Judge Error: {result.get('err')}"  
            
        # 确保data字段存在且为列表  
        if not result.get("data") or not isinstance(result["data"], list):  
            return False, "Invalid judge result format"  
            
        # 检查每个测试点  
        for i, case_result in enumerate(result["data"], 1):  
            if case_result["result"] != 0:  
                error_type = "Wrong Answer" if case_result["result"] == -1 else "Runtime Error"  
                output = case_result.get('output', 'No output available')  
                expected = test_cases[i-1].get('output', 'No expected output available')  
                return False, f"""Test case {i} failed: {error_type}  
Your output: {output}  
Expected output: {expected}"""  
        
        return True, "All test cases passed!"  
        
    except requests.exceptions.RequestException as e:  
        return False, f"Network error: {str(e)}"  
    except Exception as e:  
        return False, f"Unexpected error: {str(e)}\nType: {type(e)}"  

# 测试用代码  
if __name__ == "__main__":  
    # 测试代码  
    code = r"""  
    #include <stdio.h>  
    int main(){  
        int a, b;  
        scanf("%d%d", &a, &b);  
        printf("%d\n", a+b);  
        return 0;  
    }  
    """  

    # 测试用例  
    test_cases = [  
        {"input": "1 2\n", "output": "3"},  
        {"input": "1 9\n", "output": "11"}  
    ]  

    # 运行测试并打印详细信息  
    print("Attempting to connect to judge server...")  
    passed, message = run_c_code_in_oj(code, test_cases)  
    print(f"Passed: {passed}")  
    print(f"Message: {message}")  