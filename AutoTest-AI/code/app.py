"""Streamlit frontend for Python, Windows EXE and website smoke tests."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile

import streamlit as st
from log_analyzer import analyze_result
from multi_engine import run_executable, test_website
from test_engine import run_python_file
st.set_page_config(page_title='AutoTest-AI', page_icon='🧪', layout='wide')
st.title('🧪 AutoTest-AI | 多类型软件自动化测试平台')
st.caption('Python 脚本 / Windows EXE / 网页 URL：自动运行、检测异常、记录日志并生成报告。')
st.warning('仅运行自己编写或确认可信任的本地软件；本工具不是安全沙箱。不要将它部署成公开上传执行服务。')

kind = st.radio('选择测试对象', ['Python 脚本', 'Windows EXE', '网页 URL'], horizontal=True)
time_limit = st.slider('最长运行 / 观察时间（秒）', 1 if kind != '网页 URL' else 3, 60, 10 if kind != '网页 URL' else 15)
file = None
exe_mode = 'launch'
exe_path = ''
url = ''
if kind == 'Python 脚本':
    file = st.file_uploader('上传可信任的 .py 文件', type=['py'])
elif kind == 'Windows EXE':
    st.info('使用 EXE 的本机绝对路径；浏览器上传可能丢失 EXE 所依赖的 DLL、配置和资源文件。')
    exe_path = st.text_input('EXE 完整路径', placeholder=r'D:\Programs\MyApp\MyApp.exe')
    exe_mode = st.radio('EXE 测试模式', ['launch', 'cli'], horizontal=True,
                        format_func=lambda x: 'GUI 启动观察（推荐窗口程序）' if x == 'launch' else '命令行执行并等待退出')
    if exe_mode == 'launch':
        st.caption('观察时间结束后平台会尝试关闭被测进程；成功启动 != 软件功能正确。')
else:
    url = st.text_input('输入网页地址', value='https://example.com')
    st.caption('首次网页测试需要在终端执行：python -m playwright install chromium')

if st.button('▶ 开始测试', type='primary'):
    try:
        if kind == 'Python 脚本':
            if file is None:
                raise ValueError('请先上传 .py 文件')
            data = file.getvalue()
            if len(data) > 1024 * 1024:
                raise ValueError('演示版限制 1 MB 以内的 Python 文件')
            with tempfile.TemporaryDirectory(prefix='autotest_') as temp:
                target = Path(temp) / 'uploaded_script.py'
                target.write_bytes(data)
                with st.spinner('测试中...'):
                    result = run_python_file(target, time_limit)
                result['filename'] = file.name
                result['target_type'] = 'python'
        elif kind == 'Windows EXE':
            with st.spinner('检测 EXE...'):
                result = run_executable(exe_path.strip().strip('"'), time_limit, exe_mode)
        else:
            with st.spinner('正在检查网页...'):
                result = test_website(url.strip(), time_limit)
        result['analysis'] = analyze_result(result)
        st.session_state['last_result'] = result
    except (ValueError, RuntimeError, OSError) as exc:
        st.error(f'无法执行测试：{exc}')

if 'last_result' in st.session_state:
    r = st.session_state['last_result']
    status = r['status']
    if status in ('passed', 'launched', 'exited'):
        st.success(f'运行检测结束：{status.upper()}（不表示完整功能测试通过）')
    elif status == 'timeout':
        st.warning('运行检测超时')
    else:
        st.error(f'检测到失败或异常：{status.upper()}')
    a, b, c = st.columns(3)
    a.metric('状态', status.upper())
    b.metric('退出码', str(r.get('return_code')))
    c.metric('耗时（秒）', r.get('duration_seconds'))
    if r.get('note'):
        st.info(r['note'])
    st.subheader('📝 运行日志')
    st.text_area('stdout / 检测信息', r.get('stdout') or '（无）', height=130)
    st.text_area('stderr / 错误详情', r.get('stderr') or '（无）', height=180)
    st.subheader('🔎 错误分析')
    info = r['analysis']
    st.write(f"**错误类型：** {info['error_type']}")
    st.write(f"**解释：** {info['summary']}")
    st.write(f"**建议：** {info['suggestion']}")
    st.caption(info['analysis_mode'])
    st.download_button('⬇ 下载 JSON 测试报告', json.dumps(r, ensure_ascii=False, indent=2),
                       file_name='test_report.json', mime='application/json')
else:
    st.info('请选择测试类型，填写目标后点击开始测试。')
