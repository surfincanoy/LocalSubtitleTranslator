<div align="center">

# SRT 字幕翻译工具

基于 Ollama / llama.cpp / LM-Studio 的 SRT 字幕批量翻译工具，支持 37 种语言与中文互译。

</div>

---

## 功能特性

- **多语言支持** — 英语、日语、法语、德语、西班牙语等 37 种语言与中文互译
- **并发翻译** — 可配置并发数，多条字幕同时翻译，提升效率
- **双语字幕** — 支持输出仅译文、双语（译文在上）、双语（原文在上）三种模式
- **批量处理** — 支持选择多个 SRT 文件一次性翻译
- **多后端支持** — 支持 Ollama、llama.cpp、LM-Studio 三种后端
- **GPU 加速** — llama.cpp 支持 GPU 加速推理
- **配置管理** — 首次使用自动弹出配置对话框，配置保存到文件
- **简洁界面** — 基于 PySide6 的图形化操作界面

## 环境要求

- Python 3.10+
- 以下任一翻译后端：
  - [Ollama](https://ollama.com/) 已安装并运行
  - [llama.cpp](https://github.com/ggerganov/llama.cpp) 已编译
  - [LM-Studio](https://lmstudio.ai/) 已安装并运行

## 安装

```bash
# 克隆项目 或者 下载zip包
# 进入项目目录
cd HYMT

# 创建虚拟环境
uv venv --python 3.12

# 安装依赖
uv pip install -r requirements.txt
```

## 后端配置

### Ollama

```bash
# 安装翻译模型
ollama pull translategemma:4b
```

### llama.cpp

1. 编译 llama.cpp：
```bash
# 下载源码
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# 编译（支持 CUDA）
cmake -B build -DGGML_CUDA=ON
cmake --build build --config Release
```

2. 下载 GGUF 模型文件到指定目录（如 `/mnt/D/llama/models`）

3. 首次使用时，在配置对话框中设置：
   - 可执行文件路径
   - 模型目录
   - 端口号
   - GPU 层数
   - 上下文窗口

### LM-Studio

1. 下载并安装 [LM-Studio](https://lmstudio.ai/)
2. 启动 LM-Studio 并加载模型
3. 首次使用时，在配置对话框中设置端口号（默认 1234）

## 使用方法

### 启动 GUI

```bash
python gui.py
```

### 操作步骤

1. **选择文件** — 点击"浏览"选择一个或多个 `.srt` 字幕文件
2. **选择输出目录** — 设置翻译后文件的保存位置
3. **设置翻译方向**
   - **中译多**：中文 → 其他语言
   - **多译中**：其他语言 → 中文
4. **选择目标语言** — 从下拉框选择翻译的语言
5. **选择后端** — 选择 Ollama、llamacpp 或 lmstudio
6. **选择模型** — 从下拉框选择可用模型
7. **设置并发数** — 同时翻译的字幕条数（默认 4）
8. **选择输出模式**
   - 仅译文
   - 双语（译文在上）
   - 双语（原文在上）
9. **开始翻译** — 点击"开始翻译"按钮

## 配置文件

配置文件位于项目目录下 `llamacpp_config.json`：

```json
{
  "executable": "/mnt/D/llama/llama-server",
  "model_dir": "/mnt/D/llama/models",
  "port": 11433,
  "n_gpu_layers": 30,
  "ctx_size": 4096,
  "lmstudio_port": 1234,
  "host": "127.0.0.1",
  "lmstudio_host": "127.0.0.1"
}
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `executable` | llama-server 可执行文件路径 | `/mnt/D/llama/llama-server` |
| `model_dir` | 模型文件目录 | `/mnt/D/llama/models` |
| `port` | llama-server 端口号 | `11433` |
| `n_gpu_layers` | GPU 加速层数 | `30` |
| `ctx_size` | 上下文窗口大小 | `4096` |
| `lmstudio_port` | LM-Studio 端口号 | `1234` |
| `host` | llama-server IP 地址 | `127.0.0.1` |
| `lmstudio_host` | LM-Studio IP 地址 | `127.0.0.1` |

## 项目结构

```
HYMT/
├── backend.py              # 翻译后端（Ollama/llama.cpp/LM-Studio API 调用）
├── gui.py                  # PySide6 图形界面
├── requirements.txt        # Python 依赖
├── llamacpp_config.json    # 配置文件（自动生成）
└── README.md
```

## 输出文件命名

| 模式 | 文件名格式 | 示例 |
|------|-----------|------|
| 仅译文 | `原文件名_{语言代码}.srt` | `video_zh.srt`、`video_ja.srt` |
| 双语 | `原文件名_bilingual_{语言代码}.srt` | `video_bilingual_zh.srt` |

语言代码：`zh`=中文、`en`=英语、`ja`=日语、`fr`=法语、`de`=德语 等（遵循 ISO 639-1 标准）。

## 依赖说明

| 包 | 用途 |
|----|------|
| `PySide6` | GUI 界面框架 |
| `ollama` | Ollama API 客户端 |
| `httpx` | HTTP 客户端（llama.cpp/LM-Studio API） |
| `srt` | SRT 字幕文件解析与生成 |

## 许可证

MIT License
