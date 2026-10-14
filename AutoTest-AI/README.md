# AutoTest-AI：多类型软件自动化测试平台

> 一个基于 **Python + Streamlit + Playwright** 的轻量级软件自动化测试演示项目。支持 **Python 脚本、Windows EXE 和网页 URL** 三类测试对象，自动记录运行状态、异常信息与日志，并导出 JSON 测试报告。

## 1. 项目简介

本项目用于演示基本的软件自动化检测流程：

**选择测试对象 → 配置超时/观察时间 → 自动执行测试 → 捕获错误与日志 → 生成分析结果 → 下载 JSON 报告。**

平台使用规则对常见错误进行解释并提供建议，**当前没有接入大语言模型 API**。开发过程借助 AI 辅助，相关对话记录放在 `ai_conversation/` 中。

> **适用范围：** 本项目是课程小项目/最小可行演示系统（MVP），不是能够发现任意软件所有缺陷的通用测试平台。仅测试自己编写或确认可信任的程序，切勿把本项目部署成允许陌生用户上传并执行代码的公网服务。

## 2. 主要功能

| 测试类型 | 输入 | 主要检测项目 | 典型状态 |
| --- | --- | --- | --- |
| Python 脚本 | 上传 `.py` 文件 | 程序是否正常结束、退出码、stdout/stderr、Python 异常、超时 | `PASSED`、`FAILED`、`TIMEOUT` |
| Windows EXE | 本机 `.exe` **绝对路径** | GUI 程序启动与持续运行状态；CLI 程序的退出码、stdout/stderr、超时 | `LAUNCHED`、`EXITED`、`FAILED`、`TIMEOUT` |
| 网页 URL | `http://` 或 `https://` 地址 | 页面导航、主文档 HTTP 状态、JavaScript 页面异常、Console 错误、失败的网络请求 | `PASSED`、`FAILED`、`ERROR`、`TIMEOUT` |

其他功能：

- Streamlit 可视化界面与测试进度提示。
- 可配置运行时限（1–60 秒；网页测试 3–60 秒）。
- 自动记录检测信息、错误详情和耗时。
- 基于规则的错误分类、解释和修复建议（不是实际的大模型在线分析）。
- 下载含中文内容的 JSON 测试报告。
- 网页测试在独立 Python 子进程中运行 Playwright，以减少 Windows 上与 Streamlit 事件循环的冲突。

**状态说明：** `PASSED` 表示本次所执行的检查未发现异常，并不等于程序功能全面正确；`LAUNCHED` 表示 GUI 进程在观察时段内仍然运行，也不代表全部功能通过测试。

## 3. 项目目录

```text
AutoTest-AI/
├── README.md                    # 项目说明
├── requirements.txt             # Python 依赖
├── .gitignore
├── code/
│   ├── app.py                   # Streamlit 交互界面
│   ├── test_engine.py           # Python 脚本测试引擎
│   ├── multi_engine.py          # EXE 测试及网页子进程调度
│   ├── web_worker.py            # 独立 Playwright 网页测试进程
│   ├── log_analyzer.py          # 规则化日志与错误分析
│   ├── examples/
│   │   ├── normal_demo.py       # 正常 Python 示例
│   │   ├── error_demo.py        # 异常 Python 示例
│   │   ├── timeout_demo.py      # 超时 Python 示例
│   │   └── web_error_demo.html  # 故意触发 JS 异常的网页
│   └── tests/                   # 平台自动测试用例
├── video/                       # 自行录制的不超过 60 秒演示视频
└── ai_conversation/             # 与 AI 的完整开发沟通记录
```

`exe_error_demo.exe` 可按第 6 节自行生成；不要求把构建产物提交仓库。

## 4. 环境与安装

- 操作系统：**Windows 10/11**（EXE 测试须在 Windows 本机运行）。
- Python：**推荐 3.11**（尽量避免在不同 Python/虚拟环境之间交叉安装依赖）。
- 浏览器：网页测试由 Playwright 安装 Chromium。

在 **PowerShell** 中进入项目根目录：

```powershell
cd D:\softwareautotest\AutoTest-AI
```

建议新建虚拟环境（如果你已有可正常运行的环境，可跳过创建步骤，但后续命令应在同一环境执行）：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
```

若 PowerShell 禁止激活脚本，可以不激活，直接使用 `.\.venv\Scripts\python.exe -m pip ...` 和 `.\.venv\Scripts\python.exe -m streamlit ...`。如果没有 `py -3.11`，先安装 Python 3.11，或在确认版本后使用已有的 `python -m venv .venv`。

**运行平台：**

```powershell
python -m streamlit run code/app.py
```

浏览器访问 **http://localhost:8501**。保持运行平台的终端开启，按 `Ctrl+C` 停止。

> Playwright 安装与 Streamlit 启动应使用同一个 Python 解释器。可运行 `python -c "import sys; print(sys.executable)"` 核对。

## 5. 三类软件的使用方法

### 5.1 Python 脚本检测

1. 选择 **Python 脚本**。
2. 上传 `code/examples/normal_demo.py`，点击 **开始测试**；预期为 `PASSED`。
3. 上传 `code/examples/error_demo.py`，再次测试；预期为 `FAILED`，记录 Python 异常（如 `ZeroDivisionError`）。
4. 可以上传 `timeout_demo.py` 并缩短允许运行的时间，演示 `TIMEOUT`。

演示版限制上传的 Python 源文件大小不超过 **1 MB**。

### 5.2 Windows EXE 检测

**GUI 启动观察（launch 模式）：**

- 测试对象选择 **Windows EXE**。
- EXE 绝对路径填写 `C:\Windows\System32\notepad.exe`（Windows 自带记事本）。
- 选择 **GUI 启动观察**，观察时间如 **3 秒**，点击开始测试。
- 如果进程持续运行，预期返回 `LAUNCHED`；如果在观察窗口内退出，将返回 `EXITED`（退出码 0）或 `FAILED`（非零退出码）。
- **注意：** 当前 GUI 模式不会收集程序窗口内容、stdout/stderr；观察结束会尝试终止本次启动的根进程。某些 Windows 应用可能复用已有进程，不能仅凭这一测试断言软件全部正常。

**CLI 等待退出（cli 模式）：**

- 用于短时间运行并结束的命令行 EXE，能获取退出码、stdout 和 stderr。
- 对第 6 节构造的异常示例选择 **cli 模式**，预期获得 `FAILED`、退出码 `1` 和模拟错误日志。
- 对持续运行的 GUI 软件不要直接使用 CLI 模式；达到时间上限会报告超时。

### 5.3 网页 URL 检测

在一个**新的 PowerShell 终端**中运行本地测试网页服务：

```powershell
cd D:\softwareautotest\AutoTest-AI\code\examples
python -m http.server 8765 --bind 127.0.0.1
```

保持该终端开启。在平台中选择 **网页 URL**，输入：

```text
http://127.0.0.1:8765/web_error_demo.html
```

点击 **开始测试**。预期主页面 HTTP 状态码为 **200**，并捕获示例页面故意触发的 JavaScript 错误，整体检测结果为 **FAILED**。这意味着平台**检测成功、被测网页包含错误**，并非测试平台崩溃。

如果返回 `ERR_CONNECTION_REFUSED`，检查 8765 端口的本地服务是否仍在运行；如果是 HTTP `404`，检查是否从 `code/examples` 目录启动了 HTTP 服务器、以及 HTML 文件是否存在。

网页测试采用冒烟测试策略，**并不包含自动填写表单、点击全部按钮、验证复杂业务逻辑**等完整端到端测试功能。

## 6. 可选：自行制作一个异常 EXE 测试样例

在 `code/examples/` 新建 `exe_error_demo.py`：

```python
import sys

print("AutoTest-AI EXE test started")
print("ERROR: Simulated program failure")
sys.exit(1)
```

安装打包工具并在项目根目录生成 EXE：

```powershell
python -m pip install pyinstaller
python -m PyInstaller --onefile --console --name exe_error_demo code/examples/exe_error_demo.py
```

生成位置：`dist\exe_error_demo.exe`。在平台选择 **Windows EXE → CLI 模式**，填写该文件的绝对路径，允许 15 秒运行，预期：

```text
Status: FAILED
Return code: 1
stdout:
AutoTest-AI EXE test started
ERROR: Simulated program failure
```

首次运行 PyInstaller 打包的程序可能需要稍长的启动时间，请适当调整时限。本例用于验证非零退出码及日志收集，不代表真实软件缺陷。

## 7. 自动测试与结果报告

在项目根目录运行代码级单元测试：

```powershell
python -m unittest discover -s code/tests -p "test_*.py" -v
```

网页测试还需按第 5.3 节在本地运行浏览器端到端演示；单元测试通过不能代替真实浏览器与 EXE 验收。

平台页面展示：

- **状态**：`PASSED` / `FAILED` / `LAUNCHED` / `EXITED` / `ERROR` / `TIMEOUT` 等。
- **退出码**：Python 或 EXE 进程实际退出码；网页没有进程退出码，可能显示 `None`。
- **耗时**：本次检测的执行时长。
- **运行日志**：标准输出/检测信息、标准错误/异常信息。
- **错误分析**：基于规则给出异常类型、解释和建议。

点击 **下载 JSON 测试报告** 可保存 `test_report.json`，用于复核测试对象、状态、日志和耗时等信息。

## 8. 设计与技术实现

```text
Streamlit（app.py）
    ├── Python → test_engine.py → 运行脚本、采集退出码及日志
    ├── EXE    → multi_engine.py → subprocess 监测/采集
    └── 网页   → multi_engine.py → 独立 web_worker.py
                                         └── Playwright + Chromium
    ↓
log_analyzer.py（规则分析）
    ↓
网页展示 + JSON 报告
```

网页测试采用独立子进程，以减少 Streamlit 与 Windows asyncio 事件循环兼容问题。子进程通过 JSON 返回测试结果。Windows 下推荐统一 UTF-8 输出/输入编码，避免中文日志乱码。

## 9. 已验证的演示现象与局限

在 Windows 实机调试过程中，已观察到：

- 网页示例能够加载并返回 HTTP **200**，平台捕获了 `nonexistentFunction is not defined` JavaScript 异常，显示 `FAILED`。
- EXE 异常示例在 **GUI 观察模式**下返回非零退出码 `1`，平台显示 `FAILED`；此模式没有 stdout/stderr 输出，属于预期行为。
- Windows Playwright 的 Python 环境、独立进程路径和 UTF-8 中文乱码问题已根据实机调试进行修正。

**仍需在最终提交前复核：** Python 正常/异常样例、记事本正常 GUI 启动、EXE 异常示例 CLI 日志输出、JSON 报告下载。不要把尚未实际运行的项目标记为“全部测试通过”。

目前不支持任意软件的完整自动测试用例生成，也不支持自动验证 GUI 按钮或所有网站业务流程。规则化错误分析不应称为在线 AI 大模型诊断。

## 10. 课程提交材料

本仓库按课程要求保留三个主要文件夹：

1. **`code/`**：全部源代码、示例和测试代码。
2. **`video/`**：不超过 **60 秒**的真实本地操作录屏（建议展示 Python 异常、EXE 异常、网页 JS 异常，以及 JSON 报告）。
3. **`ai_conversation/`**：与 AI 从需求分析、代码生成到调试修改的**完整真实对话过程**，公开前应检查并遮盖密钥、隐私及敏感路径信息。

`README.md` 位于仓库根目录。上传至 **GitHub Public 仓库**后，提交仓库链接即可。README 本身不能代替实际录屏或完整 AI 对话记录，这两部分需要项目作者自行补充。

---

**项目性质：** 教学与演示用途。仅用于本地可信程序的自动化运行检查。
