"""Streamlit frontend for Python, Windows EXE and website smoke tests."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile

import streamlit as st
from log_analyzer import analyze_result
from directory_scanner import scan_directory
from multi_engine import run_executable, test_website
from test_engine import run_python_file

st.set_page_config(page_title='AutoTest-AI', page_icon='🧪', layout='wide')
st.title('🧪 AutoTest-AI | 多类型软件自动化测试平台')
st.caption('Python 脚本 / Windows EXE / 网页 URL：自动运行、检测异常、记录日志并生成报告。')
st.warning('仅运行自己编写或确认可信任的本地软件；本工具不是安全沙箱。不要将它部署成公开上传执行服务。')

kind = st.radio('选择测试对象', ['软件目录', 'Python 脚本', 'Windows EXE', '网页 URL'], horizontal=True)
time_limit = st.slider('最长运行 / 观察时间（秒）', 1 if kind != '网页 URL' else 3, 60, 10 if kind != '网页 URL' else 15)
file = None
directory_candidates = []
exe_mode = 'launch'
exe_path = ''
url = ''
if kind == '软件目录':
    st.info('输入可信任的软件目录后，点击“开始测试”将自动扫描并依次运行其中的 .py / .exe 文件，无需逐个选择。请勿输入不可信目录。')
    directory = st.text_input('待测软件所在目录', value=str(Path(__file__).resolve().parent / 'examples'))
    st.caption('自动跳过虚拟环境等目录；单次最多执行 20 个文件，避免误扫整个磁盘。')
    exe_mode = st.radio('目录中 EXE 的运行模式', ['launch', 'cli'], horizontal=True,
                        format_func=lambda m: 'GUI 启动观察' if m == 'launch' else 'CLI 捕获退出码与日志')
elif kind == 'Python 脚本':
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
        if kind == '软件目录':
            from datetime import datetime, timezone
            root = Path(directory.strip().strip('"')).expanduser().resolve()
            candidates = scan_directory(str(root))
            if not candidates:
                raise ValueError('目录中没有找到可测试的 .py 或 .exe 文件')
            if len(candidates) > 20:
                raise ValueError(f'该目录找到 {len(candidates)} 个程序，超过单次执行上限 20；请缩小目录范围')
            results = []
            progress = st.progress(0, text='准备逐个测试...')
            for index, candidate in enumerate(candidates):
                target = Path(candidate['path']).resolve()
                if not target.is_file() or not target.is_relative_to(root):
                    continue
                progress.progress(index / len(candidates), text=f"正在测试 {index+1}/{len(candidates)}：{candidate['name']}")
                try:
                    if candidate['type'] == 'python':
                        item = run_python_file(target, time_limit)
                        item['target_type'] = 'python'
                    else:
                        item = run_executable(target, time_limit, exe_mode)
                except Exception as exc:
                    item = {'filename': candidate['name'], 'target_type': candidate['type'],
                            'status': 'error', 'return_code': None, 'stdout': '',
                            'stderr': f'{type(exc).__name__}: {exc}', 'duration_seconds': 0,
                            'note': '该程序的自动执行失败，已继续测试其他文件。'}
                item['selected_entry'] = str(target)
                item['analysis'] = analyze_result(item)
                results.append(item)
            progress.progress(1.0, text='目录测试完成')
            counts = {k: sum(r['status'] == k for r in results) for k in
                      ('passed', 'failed', 'timeout', 'error', 'launched', 'exited')}
            batch = {'source_directory': str(root), 'target_type': 'directory',
                     'started_at_utc': datetime.now(timezone.utc).isoformat(),
                     'total': len(results), 'counts': counts, 'results': results}
            st.session_state['last_batch'] = batch
            st.session_state.pop('last_result', None)
        elif kind == 'Python 脚本':
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
        if kind != '软件目录':
            result['analysis'] = analyze_result(result)
            st.session_state['last_result'] = result
            st.session_state.pop('last_batch', None)
    except (ValueError, RuntimeError, OSError) as exc:
        st.error(f'无法执行测试：{exc}')

if 'last_batch' in st.session_state:
    batch = st.session_state['last_batch']
    st.subheader('📋 目录批量测试结果')
    st.write(f"扫描并测试完成：**{batch['total']} 个文件**；失败/超时/执行错误：**{batch['counts']['failed'] + batch['counts']['timeout'] + batch['counts']['error']} 个**。")
    st.dataframe([{'文件': Path(r['selected_entry']).name, '类型': r['target_type'],
                   '状态': r['status'].upper(), '退出码': r['return_code'],
                   '耗时(秒)': r['duration_seconds']} for r in batch['results']],
                 use_container_width=True, hide_index=True)
    for r in batch['results']:
        with st.expander(f"{Path(r['selected_entry']).name} — {r['status'].upper()}",
                         expanded=r['status'] in ('failed','error','timeout')):
            st.write('**stdout**')
            st.code(r.get('stdout') or '（无）')
            st.write('**stderr**')
            st.code(r.get('stderr') or '（无）')
            info = r['analysis']
            st.write(f"**错误类型：** {info['error_type']}")
            st.write(f"**分析：** {info['summary']}")
            st.write(f"**建议：** {info['suggestion']}")
    st.download_button('⬇ 下载目录批量测试 JSON 报告',
                       json.dumps(batch, ensure_ascii=False, indent=2),
                       file_name='directory_test_report.json', mime='application/json')
elif 'last_result' in st.session_state:
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
