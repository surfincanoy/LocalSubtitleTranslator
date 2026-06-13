<div align="center">

# 🎬 LocalSubtitleTranslator
# SRT 字幕翻译工具

![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/PySide6-GUI-green?logo=qt&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)

A PySide6 GUI tool for batch-translating SRT subtitle files between Chinese and 37 other languages, powered by Ollama / llama.cpp / LM-Studio backends.

基于 Ollama / llama.cpp / LM-Studio 的 SRT 字幕批量翻译工具，支持 37 种语言与中文互译。

</div>

---

<div align="center">

[English](#english) · [中文](#中文)

</div>

---

<a id="english"></a>

## ✨ Features

| Feature | Description |
|---|---|
| 🌐 **37 Languages** | Bidirectional translation between Chinese and English, Japanese, French, German, Spanish, and more |
| ⚡ **Concurrent Translation** | Configurable parallelism for faster batch processing |
| 📝 **Bilingual Subtitles** | Three output modes: translation only, bilingual (translation on top), bilingual (original on top) |
| 📁 **Batch Processing** | Translate multiple SRT files at once |
| 🔧 **Three Backends** | Ollama, llama.cpp, LM-Studio — each independently configurable |
| 🖼️ **Floating Config Panel** | Per-backend IP/port configuration in independent floating windows |
| 💾 **Persistent Selection** | Last-used backend is remembered across sessions |
| 🎨 **Clean GUI** | Built with PySide6 |

---

## 📋 Requirements

- Python 3.12+
- One of the following translation backends (manually started):
  - [Ollama](https://ollama.com/)
  - [llama.cpp](https://github.com/ggerganov/llama.cpp) (llama-server)
  - [LM-Studio](https://lmstudio.ai/)

---

## 🚀 Installation

```bash
# Clone or download the project
cd LocalSubtitleTranslator

# Create virtual environment
uv venv --python 3.12

# Install dependencies
uv pip install -r requirements.txt
```

---

## 🔌 Backend Setup

> All backends are started by the user before running the tool. The tool only connects to them via HTTP API — it does not manage backend processes.

<details>
<summary><b>Ollama</b></summary>

```bash
ollama pull translategemma:4b    # Install a translation model
ollama serve                      # Start the server (default port 11434)
```

</details>

<details>
<summary><b>llama.cpp</b></summary>

Download and load model files yourself.

**Recommended companion project:**
> [Llama-cpp-Launcher](https://github.com/surfincanoy/Llama-cpp-Launcher) — A convenient launcher for llama.cpp

Or build from source:
```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
cmake -B build -DGGML_CUDA=ON    # CUDA support
cmake --build build --config Release
./build/bin/llama-server -m /path/to/model.gguf   # Start on default port 11433
```

</details>

<details>
<summary><b>LM-Studio</b></summary>

1. Download and install [LM-Studio](https://lmstudio.ai/)
2. Load a model and start the local server (default port 1234)

</details>

---

## 💻 Usage

```bash
uv run gui.py
```

### Steps

| # | Step | Description |
|---|---|---|
| 1 | **Select files** | Click "Browse" to choose one or more `.srt` subtitle files |
| 2 | **Select output directory** | Choose where translated files are saved |
| 3 | **Translation direction** | 中译多 (Chinese → other) or 多译中 (other → Chinese) |
| 4 | **Target language** | Select from the dropdown |
| 5 | **Concurrency** | Number of simultaneous translations (default: 4) |
| 6 | **Backend** | Select Ollama, llamacpp, lmstudio, or 无 (None) |
| 7 | **Config** | If no config exists for the selected backend, a floating config window pops up. Set IP and port, click Save. |
| 8 | **Model** | Select from available models |
| 9 | **Output mode** | Translation only, bilingual (translation on top), or bilingual (original on top) |
| 10 | **Start** | Click "开始翻译" |

---

## ⚙️ Configuration

Configuration is stored in `llamacpp_config.json` in the project root.

Each backend is configured independently. When you select a backend that hasn't been configured yet, a floating config window appears. Clicking **Save** writes only that backend's entry to the config file. Switching backends does not overwrite other backends' settings.

### Config File Structure

```json
{
  "Ollama": {
    "host": "127.0.0.1",
    "port": 11434
  },
  "Llama.cpp": {
    "host": "127.0.0.1",
    "port": 11433
  },
  "Lmstudio": {
    "host": "127.0.0.1",
    "port": 1234
  },
  "_last_backend": "ollama"
}
```

### Config Fields

| Field | Description | Default |
|---|---|---|
| `Ollama.host` | Ollama server IP | `127.0.0.1` |
| `Ollama.port` | Ollama server port | `11434` |
| `Llama.cpp.host` | llama-server IP | `127.0.0.1` |
| `Llama.cpp.port` | llama-server port | `11433` |
| `Lmstudio.host` | LM-Studio IP | `127.0.0.1` |
| `Lmstudio.port` | LM-Studio port | `1234` |
| `_last_backend` | Last selected backend on startup | (empty = 无) |

### Config Behavior

- **First run** — The config file is not created automatically. When you select a backend and click Save in its config window, only that backend's entry is written.
- **Per-backend saves** — Saving Ollama's config writes `{"Ollama": {...}}`. Saving LM-Studio later appends the `Lmstudio` entry without overwriting `Ollama`.
- **Manual editing** — You can edit `llamacpp_config.json` directly. The tool reads it at runtime.
- **Delete config** — Deleting the file causes the config window to appear again when a backend is selected.

---

## 📁 Project Structure

```
LocalSubtitleTranslator/
├── backend.py              # Translation backend (API calls, SRT parsing, concurrency)
├── gui.py                  # PySide6 GUI (main window, config windows, worker thread)
├── requirements.txt        # Python dependencies
├── llamacpp_config.json    # Backend config (created on first Save)
└── README.md
```

---

## 📤 Output File Naming

| Mode | File name format | Example |
|---|---|---|
| Translation only | `{filename}_{lang_code}.srt` | `video_zh.srt`, `video_ja.srt` |
| Bilingual | `{filename}_bilingual_{lang_code}.srt` | `video_bilingual_zh.srt` |

Language codes follow ISO 639-1: `zh`=Chinese, `en`=English, `ja`=Japanese, `fr`=French, `de`=German, etc.

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `PySide6` | GUI framework |
| `httpx` | HTTP client for backend API calls |
| `srt` | SRT subtitle file parsing and generation |

---

## 📄 License

MIT License

---

<div align="center">

---

<a id="中文"></a>

## ✨ 功能特性

| 功能 | 说明 |
|---|---|
| 🌐 **37 种语言** | 英语、日语、法语、德语、西班牙语等与中文双向互译 |
| ⚡ **并发翻译** | 可配置并发数，多条字幕同时翻译，提升效率 |
| 📝 **双语字幕** | 三种输出模式：仅译文、双语（译文在上）、双语（原文在上） |
| 📁 **批量处理** | 支持选择多个 SRT 文件一次性翻译 |
| 🔧 **三种后端** | Ollama、llama.cpp、LM-Studio，每个后端独立配置 |
| 🖼️ **浮动配置面板** | 每个后端有独立的 IP/端口配置浮动窗口 |
| 💾 **持久化选择** | 记住上次使用的后端，下次启动自动恢复 |
| 🎨 **简洁界面** | 基于 PySide6 的图形化操作界面 |

---

## 📋 环境要求

- Python 3.12+
- 以下任一翻译后端（需手动启动）：
  - [Ollama](https://ollama.com/)
  - [llama.cpp](https://github.com/ggerganov/llama.cpp)（llama-server）
  - [LM-Studio](https://lmstudio.ai/)

---

## 🚀 安装

```bash
# 克隆项目或下载 zip 包
cd LocalSubtitleTranslator

# 创建虚拟环境
uv venv --python 3.12

# 安装依赖
uv pip install -r requirements.txt
```

---

## 🔌 后端配置

> 所有后端均由用户在运行工具前手动启动。工具仅通过 HTTP API 连接，不管理后端进程。

<details>
<summary><b>Ollama</b></summary>

```bash
ollama pull translategemma:4b    # 安装翻译模型
ollama serve                      # 启动服务（默认端口 11434）
```

</details>

<details>
<summary><b>llama.cpp</b></summary>

自行下载模型文件并加载。

**推荐联动项目：**
> [Llama-cpp-Launcher](https://github.com/surfincanoy/Llama-cpp-Launcher) — llama.cpp 便捷启动器

或从源码构建：
```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
cmake -B build -DGGML_CUDA=ON    # 启用 CUDA
cmake --build build --config Release
./build/bin/llama-server -m /path/to/model.gguf   # 启动服务（默认端口 11433）
```

</details>

<details>
<summary><b>LM-Studio</b></summary>

1. 下载并安装 [LM-Studio](https://lmstudio.ai/)
2. 加载模型并启动本地服务（默认端口 1234）

</details>

---

## 💻 使用方法

```bash
uv run gui.py
```

### 操作步骤

| # | 步骤 | 说明 |
|---|---|---|
| 1 | **选择文件** | 点击"浏览"选择一个或多个 `.srt` 字幕文件 |
| 2 | **选择输出目录** | 设置翻译后文件的保存位置 |
| 3 | **翻译方向** | 中译多（中文→其他语言）或多译中（其他语言→中文） |
| 4 | **目标语言** | 从下拉框选择翻译的语言 |
| 5 | **并发数** | 同时翻译的字幕条数（默认 4） |
| 6 | **后端** | 选择 ollama、llamacpp、lmstudio 或 无 |
| 7 | **配置** | 选择后端后，若该后端尚未配置，会自动弹出浮动配置窗口。设置 IP 和端口后点击"保存"。 |
| 8 | **模型** | 从下拉框选择可用模型 |
| 9 | **输出模式** | 仅译文、双语（译文在上）、双语（原文在上） |
| 10 | **开始翻译** | 点击"开始翻译"按钮 |

---

## ⚙️ 配置文件

配置文件位于项目目录下 `llamacpp_config.json`。

每个后端独立配置。选择未配置的后端时，会弹出浮动配置窗口。点击"保存"仅写入当前后端的条目，不会覆盖其他后端的配置。

### 配置文件结构

```json
{
  "Ollama": {
    "host": "127.0.0.1",
    "port": 11434
  },
  "Llama.cpp": {
    "host": "127.0.0.1",
    "port": 11433
  },
  "Lmstudio": {
    "host": "127.0.0.1",
    "port": 1234
  },
  "_last_backend": "ollama"
}
```

### 配置字段

| 字段 | 说明 | 默认值 |
|---|---|---|
| `Ollama.host` | Ollama 服务器 IP | `127.0.0.1` |
| `Ollama.port` | Ollama 端口 | `11434` |
| `Llama.cpp.host` | llama-server IP | `127.0.0.1` |
| `Llama.cpp.port` | llama-server 端口 | `11433` |
| `Lmstudio.host` | LM-Studio IP | `127.0.0.1` |
| `Lmstudio.port` | LM-Studio 端口 | `1234` |
| `_last_backend` | 启动时默认选择的后端 | （空 = 无） |

### 配置行为

- **首次运行** — 不会自动创建配置文件。选择后端并在配置窗口中点击"保存"后，仅写入该后端的条目。
- **按后端保存** — 保存 Ollama 配置写入 `{"Ollama": {...}}`，之后保存 LM-Studio 配置会追加 `Lmstudio` 条目，不会覆盖 Ollama。
- **手动编辑** — 可直接编辑 `llamacpp_config.json`，工具运行时会读取。
- **删除配置** — 删除文件后，下次选择该后端时配置窗口会再次弹出。

---

## 📁 项目结构

```
LocalSubtitleTranslator/
├── backend.py              # 翻译后端（API 调用、SRT 解析、并发控制）
├── gui.py                  # PySide6 图形界面（主窗口、配置窗口、工作线程）
├── requirements.txt        # Python 依赖
├── llamacpp_config.json    # 后端配置（首次保存时创建）
└── README.md
```

---

## 📤 输出文件命名

| 模式 | 文件名格式 | 示例 |
|---|---|---|
| 仅译文 | `原文件名_{语言代码}.srt` | `video_zh.srt`、`video_ja.srt` |
| 双语 | `原文件名_bilingual_{语言代码}.srt` | `video_bilingual_zh.srt` |

语言代码遵循 ISO 639-1 标准：`zh`=中文、`en`=英语、`ja`=日语、`fr`=法语、`de`=德语等。

---

## 📦 依赖说明

| 包 | 用途 |
|---|---|
| `PySide6` | GUI 界面框架 |
| `httpx` | HTTP 客户端，用于后端 API 调用 |
| `srt` | SRT 字幕文件解析与生成 |

---

## 📄 许可证

MIT License

</div>
