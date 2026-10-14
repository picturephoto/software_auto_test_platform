# software_auto_test_platform
关于使用AI完成软件自动化测试平台的课下小项目
# AutoTest-AI：多类型软件自动化测试平台

> 基于 **Python + Streamlit + Playwright** 的轻量级课程项目。支持**输入待测软件目录，一键批量扫描、执行并输出错误日志**；也支持单独测试 Python 脚本、Windows EXE 和网页 URL。

**项目定位**：自动化运行检查与错误捕获演示（MVP），不是能够发现任意软件全部功能缺陷的通用测试系统。开发过程中使用了 AI 辅助生成与调试代码；**当前错误分析是规则分析，没有接入在线大模型 API**。

## 1. 核心功能

- **目录自动批量测试（推荐）**：输入本地目录，点击一次“开始测试”，自动扫描其中的 `.py` 和 `.exe` 文件并依次运行，**无需逐个选择文件**。展示进度、汇总表、各文件的错误详情，支持导出批量 JSON 报告。
- **Python 脚本测试**：执行 `.py` 文件，收集退出码、stdout/stderr、Python 异常和超时信息。
- **Windows EXE 测试**：支持 GUI 启动观察（`launch`）和命令行退出/日志检测（`cli`）两种模式。
- **网页 URL 测试**：使用 Playwright + Chromium 检查页面访问、主文档 HTTP 状态、JavaScript 页面异常及控制台/请求错误。
- **错误分析与报告**：对检测结果做规则化分类、说明与建议，导出 UTF-8 JSON 报告。

### 状态含义

| 状态 | 含义 |
| --- | --- |
| `PASSED` | 本次执行的检查未发现异常，不代表功能全面正确 |
| `FAILED` | 程序非零退出，或网页检测发现错误等 |
| `TIMEOUT` | 达到配置的运行时限；不一定是程序 Bug |
| `ERROR` | 测试执行过程出现错误（例如启动失败） |
| `LAUNCHED` | GUI EXE 在观察期内持续运行；不是功能测试通过 |
| `EXITED` | GUI EXE 在观察期内以退出码 0 结束 |

## 2. 项目结构

```text
AutoTest-AI/
├── README.md                 # 本说明文件
├── requirements.txt          # 运行依赖
├── .gitignore
├── code/
│   ├── app.py                # Streamlit 页面与目录批量执行流程
│   ├── directory_scanner.py  # 目录扫描：查找 .py / .exe
│   ├── test_engine.py        # Python 脚本运行、日志及异常检测
│   ├── multi_engine.py       # EXE 测试与网页测试子进程调度
│   ├── web_worker.py         # 独立 Playwright 网页测试进程
│   ├── log_analyzer.py       # 规则化错误解释
│   ├── examples/             # 正常、异常、超时及网页示例
│   └── tests/                # 单元测试
├── video/                    # 自行录制的不超过 60 秒演示视频
└── prompt/                   # 使用 AI 开发、调试的真实完整对话记录
```

> `video/` 与 `prompt/` 中的演示视频、对话记录需要作者实际补充。上传公开仓库之前，请检查记录中是否含有密钥、账号或敏感信息。

## 3. 运行环境与安装

推荐 **Windows 10/11 + Python 3.11**；EXE 测试只能在 Windows 系统上进行。使用 PowerShell，在项目根目录执行：

```powershell
cd D:\softwareautotest\AutoTest-AI
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
```

如果已有可用 Python 环境，可以不重新创建虚拟环境，但安装依赖与启动平台应始终使用**同一 Python 解释器**。如果 PowerShell 不允许激活脚本，可直接调用 `.\.venv\Scripts\python.exe` 代替 `python`。

启动平台：

```powershell
python -m streamlit run code/app.py
```

浏览器打开 `http://localhost:8501`。运行期间保持终端开启，需要结束时按 `Ctrl+C`。

## 4. 使用说明

### 4.1 软件目录一键批量检测（课程要求的主要演示方式）

1. 在平台选择 **“软件目录”**。
2. 在“待测软件所在目录”中输入一个**可信任的本地文件夹**，例如：

   ```text
   D:\softwareautotest\AutoTest-AI\code\examples
   ```

3. 设置最长运行/观察时间。目录包含 EXE 时，选择统一的 **GUI 启动观察（launch）** 或 **CLI 捕获退出码与日志（cli）** 模式。
4. 点击 **“开始测试”**。平台自动扫描并逐个运行找到的 `.py` 和 `.exe` 文件，**不会再要求选择单个文件**。
5. 查看批量汇总表（文件、类型、状态、退出码、耗时），展开失败或超时记录查看 stdout、stderr、错误解释与建议。
6. 点击 **“下载目录批量测试 JSON 报告”**，获得 `directory_test_report.json`。

扫描器最多深入子目录 **4 层**，忽略 `.venv`、`venv`、`node_modules`、`build`、`dist` 等目录；单次执行最多 **20 个候选程序**，超过时会提示缩小扫描范围。**扫描是自动的，执行从点击按钮后开始；不是后台持续监控。**

**安全提示：** 目录模式会执行扫描到的所有 `.py` / `.exe` 候选文件，不会区分主程序、辅助脚本或安装程序。务必只选取**自己编写或确认可信、且适合批量运行**的测试目录；不要选系统目录、下载目录或来源不明的软件目录。本项目不提供安全沙箱。

### 4.2 单独测试 Python 脚本

选择 **“Python 脚本”**，上传 `.py` 文件（演示版最大 1 MB），点击“开始测试”。可使用：

| 示例 | 预期结果 |
| --- | --- |
| `code/examples/normal_demo.py` | `PASSED`，退出码 0 |
| `code/examples/error_demo.py` | `FAILED`，捕获 Python 异常 |
| `code/examples/timeout_demo.py` | 设置较短时限后显示 `TIMEOUT` |

### 4.3 单独测试 Windows EXE

选择 **“Windows EXE”**，输入程序的本机绝对路径，并选择模式：

- **GUI 启动观察（launch）**：例如 `C:\Windows\System32\notepad.exe`，观察 3 秒。若进程持续运行，通常显示 `LAUNCHED`；GUI 模式不采集窗口内容、stdout/stderr，并会尝试结束本次启动的根进程。
- **CLI 等待退出（cli）**：适合短时运行的命令行程序，可以捕获退出码与 stdout/stderr。不要将需要持续运行的 GUI 软件直接视为 CLI 测试对象。

如需生成一个可控的异常 EXE，在 `code/examples/` 新建 `exe_error_demo.py`：

```python
import sys

print("AutoTest-AI EXE test started")
print("ERROR: Simulated program failure")
sys.exit(1)
```

在项目根目录运行：

```powershell
python -m pip install pyinstaller
python -m PyInstaller --onefile --console --name exe_error_demo code/examples/exe_error_demo.py
```

产物通常是 `dist\exe_error_demo.exe`。选择 **CLI 模式** 并填写其绝对路径，预期显示 `FAILED`、退出码 `1` 和两行模拟日志。若要在“目录批量测试”中同时测试该 EXE，应将其**复制到单独的可信演示目录**，因为目录扫描默认忽略 `dist/` 文件夹。

### 4.4 单独测试网页 URL

先开一个新的 PowerShell 终端，在包含示例 HTML 的目录启动本地服务器：

```powershell
cd D:\softwareautotest\AutoTest-AI\code\examples
python -m http.server 8765 --bind 127.0.0.1
```

保持服务器运行。在平台中选择 **“网页 URL”**，输入：

```text
http://127.0.0.1:8765/web_error_demo.html
```

点击“开始测试”。预期：主页面 HTTP 状态 `200`，但示例网页故意触发 `JavaScript: nonexistentFunction is not defined`，所以结果为 `FAILED`。这表示**平台成功发现了被测网页中的错误**，不是平台崩溃。

如果出现 `ERR_CONNECTION_REFUSED`，先检查本地服务器是否还在运行；若显示 `404`，确认服务器工作目录中确有 `web_error_demo.html`。此功能是网页冒烟检测，并不覆盖完整业务交互。

## 5. 测试与报告

运行代码级单元测试：

```powershell
python -m unittest discover -s code/tests -p "test_*.py" -v
```

单元测试不能替代 Windows EXE 与 Chromium 的实际验收。平台提供两种报告：

- **单对象报告**：`test_report.json`，保存测试状态、日志、耗时及规则分析。
- **目录批量报告**：`directory_test_report.json`，保存扫描目录、执行数量、各状态统计及每个程序的详细结果。

### 已有实际演示结果

在课程项目调试中，已观察到：

- 本地网页返回 HTTP `200`，平台识别出 `nonexistentFunction is not defined` 的 JavaScript 异常。
- 自制异常 EXE 返回退出码 `1`，平台识别为 `FAILED`。
- 目录批量演示扫描并执行 **5 个文件**：`normal_demo.py` 为 `PASSED`；`error_demo.py`、`exe_error_demo.py`、`exe_error_demo.exe` 为 `FAILED`；`timeout_demo.py` 为 `TIMEOUT`。
- 已处理 Windows 下 Playwright 独立子进程调用及中文编码显示问题。

以上为**特定演示样例的运行检查结果**；对真实第三方软件并不保证同样的检测覆盖率。最终上传前仍需确认导出的 JSON 可打开、日志与演示录像一致。

## 6. 技术架构

```text
Streamlit 页面 (app.py)
├── 软件目录 → directory_scanner.py
│               ├── .py → test_engine.py
│               └── .exe → multi_engine.py
├── 单独 Python → test_engine.py
├── 单独 EXE    → multi_engine.py
└── 单独网页   → multi_engine.py → web_worker.py → Playwright / Chromium
                         ↓
               日志与结果 + log_analyzer.py（规则分析）
                         ↓
                  Streamlit 展示 / JSON 导出
```

网页测试通过独立 Python 子进程运行 Playwright，减少与 Streamlit/Windows asyncio 事件循环之间的冲突，子进程通过 JSON 返回结果。通信采用 UTF-8 以正确处理中文日志。

## 7. 已知局限与安全说明

- 自动扫描只覆盖 `.py`、`.exe`，不自动测试目录中的所有软件格式，也不自动寻找“正确的启动入口”。
- 程序返回非零退出码或超时只是异常线索；`PASSED` 和 `LAUNCHED` 不代表没有功能 Bug。
- EXE 的 GUI 模式不自动点击按钮、检查窗口控件或收集完整系统崩溃转储。
- 网页模式只做加载、HTTP/JS/Console/网络错误等冒烟测试，不保证业务功能正确。
- 当前没有使用在线大模型 API；规则分析建议只能作为排查线索。
- **不要运行不可信目录，不要把可执行测试功能直接开放到公网。**

## 8. 课程提交说明

按照老师 PPT 的要求，仓库根目录应包含 `README.md` 以及三个指定文件夹：

| 目录 | 内容 |
| --- | --- |
| `code/` | 软件测试平台源代码、测试引擎、示例与单元测试 |
| `video/` | 自己真实运行平台并测试软件的录像，**不超过 60 秒** |
| `prompt/` | 与大模型交互完成开发、修改和调试的**完整真实对话过程** |

**一分钟视频建议**：展示输入测试目录 → 自动扫描批量运行 → `PASSED` / `FAILED` / `TIMEOUT` 汇总 → 展开异常日志 → 下载批量 JSON 报告。时间充足时补充网页 JavaScript 错误检测。最后将以上文件上传至 **GitHub Public 仓库**并提交仓库链接。

---

**仅限课程演示与本地可信软件运行检查。**
