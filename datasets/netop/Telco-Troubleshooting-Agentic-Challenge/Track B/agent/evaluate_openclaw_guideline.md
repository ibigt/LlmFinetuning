# Additional guidelines to run Openclaw Agent

This repository contains a Python-based batch inference pipeline for evaluating the openclaw AI agent against the CTBench dataset.

The script automates the process of loading questions from a local JSON file, invoking the Node.js-based agent, extracting the structured answers, and compiling the results into a CSV format suitable for downstream evaluation.

## **Features**

* **Local JSON Processing:** Reads benchmark tasks directly from a locally stored JSON file format without needing an external API.  
* **Concurrent Execution:** Supports multithreading to evaluate multiple questions simultaneously, significantly speeding up the benchmark process.  
* **Resumable Operations:** Tracks progress automatically using the id field. If the script is interrupted, you can resume exactly where it left off without re-running completed scenarios.  
* **Robust Error Handling & Timeouts:** Implements strict timeouts (default 10 minutes per question) and force-kill mechanisms to prevent hanging processes.  
* **Answer Extraction:** Uses regex patterns to extract specific structured reasoning paths (e.g., A(1) \-\> B(2)) or falls back to the agent's complete final response.

## **Prerequisites**

Before running the script, ensure you have the following installed and configured:

* **Python 3.8+**  
* **Node.js** (Required to execute the openclaw agent)  
* **Openclaw Agent:** The openclaw repository must be cloned and accessible on your local machine.

*Note: Since the script reads from a local file, third-party networking libraries like requests are no longer required.*

## **Input Data Format**

The script expects a JSON file containing an array of task objects. Each object must contain a nested task object with both an id (integer) and a question (string).

**Example questions.json:**

\[  
  {  
    "scenario\_id": "535afb0d-fa81-419b-9bcc-b456d032df5d",  
    "task": {  
      "question": "The link planning data of Gamma-Aegis-01 within the Big Data Zone has been accidentally deleted...",  
      "id": 1  
    }  
  }  
\]

*(The script parses task.id as the primary identifier for saving files, tracking progress, and building the output CSV.)*

## **Configuration**

Before the first run, you **must** update the absolute directory paths at the top of the Python script:

\# \============================================================  
\# Configuration  
\# \============================================================

\# Default input JSON file path  
DEFAULT\_INPUT\_JSON \= "questions.json"

\# Set this to the absolute path of your openclaw project directory  
OPENCLAW\_DIR \= r"C:\\path\\to\\your\\openclaw" 

\# Set this to the absolute path where openclaw stores its session logs  
OPENCLAW\_SESSION\_DIR \= r"C:\\Users\\YourUser\\.openclaw\\agents\\main\\sessions" 

FORCE\_KILL\_TIMEOUT \= 600  \# Timeout per question in seconds  
DEFAULT\_CONCURRENCY \= 2   \# Number of parallel agent executions

## **Usage**

Run the script from the command line using various arguments to control the batch job. By default, it will attempt to process every scenario found in the specified JSON file.

### **Command Line Arguments**

| Argument | Type | Default | Description |
| :---- | :---- | :---- | :---- |
| \-i, \--input | str | questions.json | The path to the input JSON file containing the scenarios. |
| \--questions | str | None | A comma-separated list of specific ids to run. If not provided, all tasks in the file are executed. |
| \--concurrency | int | 2 | Number of concurrent agent invocations. |
| \--resume | flag | False | If passed, skips previously completed IDs based on progress.json. |

### **Examples**

```bash
# Install Python dependencies
pip install -r agent/requirements.txt

# Run all questions from the input JSON
python agent/evaluate_openclaw.py -i data/Phase_1/test.json

# Run specific questions only
python agent/evaluate_openclaw.py -i data/Phase_1/test.json --questions 1,2,5

# Run with concurrency (max 2 for competition compliance)
python agent/evaluate_openclaw.py -i data/Phase_1/test.json --concurrency 2

# Resume from an interrupted run
python agent/evaluate_openclaw.py -i data/Phase_1/test.json --resume
```

## **Output Files**

The script automatically generates an eval\_results directory in the same folder as the script. It contains the following files:

* **result.csv**: The primary output file containing the extracted answers.  
  * **Headers:** id, prediction (where id maps to the task.id from the JSON).  
* **eval\_detail.jsonl**: A JSON Lines log file containing granular details for every processed task, including timestamps, full agent payloads, success status, and execution duration. Highly useful for debugging failed runs.  
* **progress.json**: An internal state file used to track completed ids for the \--resume feature.  
* **\_msg\_\<id\>.txt & \_invoke\_wrapper.js**: Temporary files generated during execution to pass prompts to the Node.js process.

## **Troubleshooting**

* **Script gets stuck indefinitely:** Check the FORCE\_KILL\_TIMEOUT variable. Ensure you have the necessary permissions to execute task kill commands (Windows taskkill or Unix killpg).  
* **Empty prediction in CSV:** This usually means the agent failed to generate a response, or the session log file could not be found. Check OPENCLAW\_SESSION\_DIR and the eval\_detail.jsonl file for specific error messages.  
* **Invalid JSON Structure Warning:** If the script prints Skipping invalid item in JSON, double-check that your JSON format strictly follows the nested structure where task.id and task.question exist.



# OpenClaw智能体运行补充指南
本仓库包含一套基于Python的批量推理流程，用于在CTBench数据集上评测OpenClaw人工智能智能体。

该脚本可自动化完成以下流程：从本地JSON文件加载题目、调用基于Node.js的智能体、提取结构化答案，并将结果编译为适用于后续评测的CSV格式文件。

---

## 核心功能
- **本地JSON处理**：直接从本地存储的JSON文件读取评测任务，无需依赖外部API。
- **并发执行**：支持多线程同时评测多道题目，大幅提升评测流程速度。
- **断点续跑**：通过`id`字段自动追踪执行进度。若脚本中断，可从中断处精准恢复，无需重新运行已完成的场景。
- **稳健的异常处理与超时机制**：配置严格超时（默认每题10分钟）与强制终止机制，防止进程卡死。
- **答案提取**：通过正则表达式提取指定的结构化推理路径（如`A(1) -> B(2)`），若无则 fallback 提取智能体最终完整响应。

---

## 前置条件
运行脚本前，请确保已安装并配置以下环境：
1. Python 3.8及以上版本
2. Node.js（运行OpenClaw智能体必需）
3. OpenClaw智能体：需在本地克隆OpenClaw仓库并可正常访问

> 注意：由于脚本读取本地文件，**无需**安装`requests`等第三方网络库。

---

## 输入数据格式
脚本要求输入JSON文件为**任务对象数组**，每个对象必须包含嵌套的`task`对象，且包含`id`（整数）和`question`（字符串）字段。

### 示例 questions.json
```json
[
{
"scenario_id": "535afb0d-fa81-419b-9bcc-b456d032df5d",
"task": {
"question": "大数据区域内Gamma-Aegis-01的链路规划数据被意外删除……",
"id": 1
}
}
]
```
（脚本将`task.id`作为文件保存、进度追踪和输出CSV的唯一标识）

---

## 配置说明
首次运行前，**必须修改Python脚本顶部的绝对路径配置**：
```python
# ============================================================
# 配置项
# ============================================================

# 默认输入JSON文件路径
DEFAULT_INPUT_JSON = "questions.json"

# 设置为你的OpenClaw项目目录绝对路径
OPENCLAW_DIR = r"C:\path\to\your\openclaw"

# 设置为OpenClaw存储会话日志的绝对路径
OPENCLAW_SESSION_DIR = r"C:\Users\YourUser\.openclaw\agents\main\sessions"

FORCE_KILL_TIMEOUT = 600  # 单题超时时间（秒）
DEFAULT_CONCURRENCY = 2    # 智能体并行执行数量
```

---

## 使用方法
通过命令行运行脚本，搭配不同参数控制批量任务。默认会处理指定JSON文件中的所有场景。

### 命令行参数
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| -i, --input | 字符串 | questions.json | 包含测试场景的输入JSON文件路径 |
| --questions | 字符串 | 无 | 逗号分隔的指定题目ID列表；不填则执行文件中所有任务 |
| --concurrency | 整数 | 2 | 智能体并发调用数量 |
| --resume | 标记 | False | 传入该参数时，根据progress.json跳过已完成的ID |

### 运行示例
```bash
# 安装Python依赖
pip install -r agent/requirements.txt

# 运行输入JSON中的全部题目
python agent/evaluate_openclaw.py -i data/Phase_1/test.json

# 仅运行指定题目
python agent/evaluate_openclaw.py -i data/Phase_1/test.json --questions 1,2,5

# 并发运行（竞赛要求最大并发数为2）
python agent/evaluate_openclaw.py -i data/Phase_1/test.json --concurrency 2

# 中断后断点续跑
python agent/evaluate_openclaw.py -i data/Phase_1/test.json --resume
```

---

## 输出文件
脚本会在自身所在目录自动生成`eval_results`文件夹，包含以下文件：
1. **result.csv**：核心输出文件，包含提取的答案
   - 表头：`id, prediction`（`id`对应JSON中的`task.id`）
2. **eval_detail.jsonl**：JSON行格式日志，记录每道任务的时间戳、智能体完整载荷、执行状态、耗时，用于调试失败任务
3. **progress.json**：内部状态文件，用于`--resume`断点续跑
4. **_msg_<id>.txt & _invoke_wrapper.js**：执行过程中生成的临时文件，用于向Node.js进程传递指令

---

## 故障排查
1. **脚本无限卡死**
   检查`FORCE_KILL_TIMEOUT`变量；确保拥有执行进程终止命令的权限（Windows：taskkill；Unix：killpg）。

2. **CSV中prediction为空**
   通常表示智能体未生成响应，或会话日志文件未找到。检查`OPENCLAW_SESSION_DIR`路径与`eval_detail.jsonl`中的具体报错。

3. **JSON结构无效警告**
   若脚本打印`Skipping invalid item in JSON`，请检查JSON格式是否严格遵循嵌套结构，确保包含`task.id`和`task.question`字段。