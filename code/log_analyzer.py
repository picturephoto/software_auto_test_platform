"""Explain common Python errors using deterministic rules (not an LLM)."""
from __future__ import annotations
import re
from typing import Any

ERRORS = {
    'ZeroDivisionError': ('除零错误', '检查分母是否为 0，增加输入校验。'),
    'NameError': ('变量或函数名未定义', '检查变量拼写以及定义和作用域。'),
    'TypeError': ('类型不匹配', '检查参与运算的类型、函数参数和返回值。'),
    'ValueError': ('值不合法', '检查参数范围和输入格式。'),
    'IndexError': ('列表索引越界', '检查索引是否在有效范围。'),
    'KeyError': ('字典键不存在', '考虑使用 dict.get() 或检查键。'),
    'FileNotFoundError': ('文件不存在', '检查相对路径、工作目录和文件名。'),
    'ModuleNotFoundError': ('缺少 Python 模块', '检查依赖安装情况和 Python 解释器环境。'),
    'ImportError': ('模块导入失败', '检查导入名称、安装版本和模块路径。'),
    'AssertionError': ('断言失败', '检查程序输出与断言的预期是否一致。'),
    'SyntaxError': ('语法错误', '检查报错位置附近的括号、缩进与语法。'),
    'IndentationError': ('缩进错误', '统一代码块缩进，避免混用 Tab 和空格。'),
    'PermissionError': ('权限不足', '检查文件或目录访问权限。'),
    'RuntimeError': ('运行时错误', '结合完整堆栈检查触发条件。'),
}


def analyze_result(result: dict[str, Any]) -> dict[str, str]:
    status = result['status']
    if status == 'launched':
        return {'error_type': '无启动错误', 'summary': 'EXE 在观察窗口内保持运行。', 'suggestion': '需要额外 UI 操作及断言才能验证业务功能。', 'analysis_mode': '规则分析（非大模型）'}
    if status == 'exited':
        return {'error_type': '正常退出', 'summary': '程序在观察窗口内以退出码 0 结束。', 'suggestion': '进一步执行功能用例以验证正确性。', 'analysis_mode': '规则分析（非大模型）'}
    if result.get('target_type') == 'website':
        errors = result.get('console_errors', [])
        return {'error_type': 'WebPageError' if errors else ('WebTimeout' if status == 'timeout' else '网页检测结果'), 'summary': '；'.join(errors[:3]) if errors else f'网页测试状态：{status}', 'suggestion': '检查网页地址、开发者工具 Console/Network 和浏览器依赖；必要时补充交互断言。', 'analysis_mode': '规则分析（非大模型）'}
    if status == 'passed':
        return {'error_type': '无', 'summary': '进程正常退出，未检测到运行时异常。',
                'suggestion': '这只是运行冒烟测试；业务正确性仍需要断言或功能测试。',
                'analysis_mode': '规则分析（非大模型）'}
    if status == 'timeout':
        return {'error_type': 'Timeout', 'summary': '程序超过最大运行时长。',
                'suggestion': '检查死循环、阻塞输入、网络请求或设置更合适的超时时间。',
                'analysis_mode': '规则分析（非大模型）'}
    stderr = result.get('stderr', '')
    # Python tracebacks usually end with "ErrorName: details".
    matches = re.findall(r'^([A-Za-z_][A-Za-z_0-9]*(?:Error|Exception|Warning))(?::|$)', stderr, re.M)
    error_type = matches[-1] if matches else ('ProcessError' if status == 'failed' else 'LaunchError')
    meaning, suggestion = ERRORS.get(error_type, ('程序运行失败', '查看标准错误日志与退出码，定位异常发生位置。'))
    return {'error_type': error_type, 'summary': meaning, 'suggestion': suggestion,
            'analysis_mode': '规则分析（非大模型）'}
