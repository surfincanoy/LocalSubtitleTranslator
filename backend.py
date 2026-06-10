import srt
from concurrent.futures import ThreadPoolExecutor
import httpx
import subprocess
import time
import signal
import os
import json
from pathlib import Path

LANGUAGES = {
    "英语": "en",
    "法语": "fr",
    "葡萄牙语": "pt",
    "西班牙语": "es",
    "日语": "ja",
    "土耳其语": "tr",
    "俄语": "ru",
    "阿拉伯语": "ar",
    "韩语": "ko",
    "泰语": "th",
    "意大利语": "it",
    "德语": "de",
    "越南语": "vi",
    "马来语": "ms",
    "印尼语": "id",
    "菲律宾语": "tl",
    "印地语": "hi",
    "繁体中文": "zh-Hant",
    "波兰语": "pl",
    "捷克语": "cs",
    "荷兰语": "nl",
    "高棉语": "km",
    "缅甸语": "my",
    "波斯语": "fa",
    "古吉拉特语": "gu",
    "乌尔都语": "ur",
    "泰卢固语": "te",
    "马拉地语": "mr",
    "希伯来语": "he",
    "孟加拉语": "bn",
    "泰米尔语": "ta",
    "乌克兰语": "uk",
    "藏语": "bo",
    "哈萨克语": "kk",
    "蒙古语": "mn",
    "维吾尔语": "ug",
    "粤语": "yue",
    "简体中文": "zh",
}


def list_ollama_models():
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            models = []
            for line in lines[1:]:
                parts = line.split()
                if parts:
                    models.append(parts[0])
            return models
    except (OSError, FileNotFoundError):
        pass
    return []


CONFIG_FILE = Path(__file__).parent / "llamacpp_config.json"

DEFAULT_CONFIG = {
    "executable": "/mnt/D/llama/llama-server",
    "model_dir": "/mnt/D/llama/models",
    "port": 11433,
    "n_gpu_layers": 30,
    "ctx_size": 4096,
    "lmstudio_port": 1234,
    "host": "127.0.0.1",
    "lmstudio_host": "127.0.0.1",
}


def load_llamacpp_config():
    """加载 llamacpp 配置"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            for key, value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = value
            return config
        except (json.JSONDecodeError, OSError):
            pass
    return DEFAULT_CONFIG.copy()


def save_llamacpp_config(config):
    """保存 llamacpp 配置"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except OSError:
        return False


_llama_server_process = None


def start_llama_server(
    model_name,
    model_dir="/mnt/D/llama/models",
    host="127.0.0.1",
    port=11433,
    n_gpu_layers=30,
    ctx_size=4096,
    executable="/mnt/D/llama/llama-server",
):
    """启动 llama-server 进程"""
    global _llama_server_process
    
    if _llama_server_process and _llama_server_process.poll() is None:
        print("llama-server 已在运行")
        return True
    
    model_path = os.path.join(model_dir, model_name)
    if not os.path.exists(model_path):
        if not model_name.endswith(".gguf"):
            model_path = os.path.join(model_dir, f"{model_name}.gguf")
    
    if not os.path.exists(model_path):
        print(f"模型文件不存在: {model_path}")
        return False
    
    if not os.path.exists(executable):
        print(f"llama-server 不存在: {executable}")
        return False
    
    cmd = [
        executable,
        "-m", model_path,
        "--host", host,
        "--port", str(port),
        "-c", str(ctx_size),
        "--n-gpu-layers", str(n_gpu_layers),
    ]
    
    try:
        env = os.environ.copy()
        lib_dir = str(Path(executable).parent)
        env["LD_LIBRARY_PATH"] = lib_dir + (":" + env.get("LD_LIBRARY_PATH", ""))
        _llama_server_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        
        if wait_for_server(host, port):
            print(f"llama-server 启动成功，PID: {_llama_server_process.pid}")
            return True
        else:
            print("llama-server 启动超时")
            stop_llama_server()
            return False
    except (OSError, FileNotFoundError) as e:
        print(f"启动 llama-server 失败: {e}")
        return False


def stop_llama_server():
    """停止 llama-server 进程"""
    global _llama_server_process
    
    if _llama_server_process:
        try:
            _llama_server_process.terminate()
            _llama_server_process.wait(timeout=5)
            print("llama-server 已停止")
        except (subprocess.TimeoutExpired, OSError):
            _llama_server_process.kill()
            print("llama-server 已强制停止")
        finally:
            _llama_server_process = None


def wait_for_server(host="127.0.0.1", port=11433, timeout=30):
    """等待 llama-server 就绪"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = httpx.get(f"http://{host}:{port}/v1/models", timeout=2.0)
            if response.status_code == 200:
                return True
        except (httpx.RequestError, httpx.HTTPStatusError):
            pass
        time.sleep(0.5)
    return False


def list_llamacpp_models(host="127.0.0.1", port=11433, model_dir="/mnt/D/llama/models"):
    """列出可用的 llama-server 模型"""
    models = []
    
    # 尝试从运行中的服务器获取模型列表
    try:
        response = httpx.get(f"http://{host}:{port}/v1/models", timeout=2.0)
        if response.status_code == 200:
            data = response.json()
            models = [m["id"] for m in data.get("data", [])]
    except (httpx.RequestError, httpx.HTTPStatusError):
        pass
    
    # 扫描本地模型目录
    if os.path.exists(model_dir):
        for f in os.listdir(model_dir):
            if f.endswith(".gguf"):
                model_name = f[:-5]  # 移除 .gguf 后缀
                if model_name not in models:
                    models.append(model_name)
    
    return models


def list_lmstudio_models(host="127.0.0.1", port=1234):
    """列出 LM-Studio 可用模型"""
    models = []
    try:
        response = httpx.get(f"http://{host}:{port}/v1/models", timeout=2.0)
        if response.status_code == 200:
            data = response.json()
            models = [m["id"] for m in data.get("data", [])]
    except (httpx.RequestError, httpx.HTTPStatusError):
        pass
    return models


def _lmstudio_translate(text, target_lang, model_name, host="127.0.0.1", port=1234):
    """通过 LM-Studio API 翻译"""
    tgt_code = LANGUAGES.get(target_lang, "zh")
    
    prompt = (
        f"You are a professional translator to {target_lang} ({tgt_code}).\n"
        f"Produce only the {target_lang} translation, no explanations.\n\n{text}"
    )
    
    response = httpx.post(
        f"http://{host}:{port}/v1/chat/completions",
        json={
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024,
        },
        timeout=60.0,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def _ollama_translate(text, target_lang, model_name):
    import ollama

    tgt_code = LANGUAGES.get(target_lang, "zh")

    prompt = (
        f"You are a professional translator to {target_lang} ({tgt_code}).\n"
        f"Produce only the {target_lang} translation, no explanations.\n\n{text}"
    )

    response = ollama.chat(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
    )
    return response["message"]["content"].strip()


def _llamacpp_translate(text, target_lang, model_name, host="127.0.0.1", port=11433):
    """通过 llama-server HTTP API 翻译"""
    tgt_code = LANGUAGES.get(target_lang, "zh")

    prompt = (
        f"You are a professional translator to {target_lang} ({tgt_code}).\n"
        f"Produce only the {target_lang} translation, no explanations.\n\n{text}"
    )

    response = httpx.post(
        f"http://{host}:{port}/v1/chat/completions",
        json={
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024,
        },
        timeout=60.0,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def translate_srt_file(
    srt_path,
    target_lang,
    model_name,
    batch_size=1,
    mode="translation",
    reverse=False,
    output_path=None,
    progress_callback=None,
    log_callback=None,
    backend="ollama",
    host="127.0.0.1",
    port=11433,
):
    def log(msg):
        if log_callback:
            log_callback(msg)

    try:
        with open(srt_path, "r", encoding="utf-8-sig") as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(srt_path, "r", encoding="utf-8") as f:
            content = f.read()

    try:
        subs = list(srt.parse(content))
    except Exception as e:
        log(f"SRT 解析失败: {e}")
        return

    log(f"共 {len(subs)} 条字幕，开始翻译...")

    total = len(subs)
    translations = [""] * total
    done_count = 0

    def translate_one(i):
        nonlocal done_count
        text = subs[i].content.strip()
        if not text:
            done_count += 1
            if progress_callback:
                progress_callback(done_count, total)
            return
        try:
            if backend == "llamacpp":
                translations[i] = _llamacpp_translate(
                    text, target_lang, model_name, host, port
                )
            elif backend == "lmstudio":
                translations[i] = _lmstudio_translate(
                    text, target_lang, model_name, host, port
                )
            else:
                translations[i] = _ollama_translate(text, target_lang, model_name)
        except (OSError, RuntimeError, ValueError, httpx.RequestError) as e:
            log(f"第 {i + 1} 条翻译失败: {e}")
            translations[i] = text
        done_count += 1
        if progress_callback:
            progress_callback(done_count, total)

    indices = [i for i in range(total) if subs[i].content.strip()]
    with ThreadPoolExecutor(max_workers=batch_size) as executor:
        executor.map(translate_one, indices)

    new_subs = []
    for i, sub in enumerate(subs):
        if translations[i]:
            sub.content = translations[i]
        new_subs.append(sub)

    if output_path is None:
        from pathlib import Path

        p = Path(srt_path)
        target_code = LANGUAGES.get(target_lang, target_lang)
        suffix = f"_bilingual_{target_code}" if mode == "bilingual" else f"_{target_code}"
        output_path = str(p.with_name(f"{p.stem}{suffix}{p.suffix}"))

    if mode == "bilingual":
        for i, sub in enumerate(new_subs):
            orig = subs[i].content.strip()
            trans = sub.content.strip()
            if reverse:
                sub.content = f"{orig}\n{trans}"
            else:
                sub.content = f"{trans}\n{orig}"

    from pathlib import Path as _P

    out = _P(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(srt.compose(new_subs), encoding="utf-8")

    log(f"已保存: {output_path}")
    return str(output_path)
