import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import srt

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


def list_ollama_models(host=None, port=None):
    """列出 Ollama 可用模型"""
    host, port = _resolve_host_port("Ollama", host, port)
    models = []
    try:
        response = httpx.get(f"http://{host}:{port}/api/tags", timeout=2.0)
        if response.status_code == 200:
            data = response.json()
            models = [m["name"] for m in data.get("models", [])]
    except (httpx.RequestError, httpx.HTTPStatusError):
        pass
    return models


CONFIG_FILE = Path(__file__).parent / "llamacpp_config.json"

DEFAULT_CONFIG = {
    "Ollama": {
        "port": 11434,
        "host": "127.0.0.1",
    },
    "Llama.cpp": {
        "port": 11433,
        "host": "127.0.0.1",
    },
    "Lmstudio": {
        "port": 1234,
        "host": "127.0.0.1",
    },
}


def load_llamacpp_config():
    """加载配置，文件不存在时只返回默认值，不创建文件"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            for key, value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = value
                else:
                    for sub_key, sub_value in value.items():
                        if sub_key not in config[key]:
                            config[key][sub_key] = sub_value
            return config
        except (json.JSONDecodeError, OSError):
            pass
    return DEFAULT_CONFIG.copy()


def save_llamacpp_config(config):
    """保存配置"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except OSError:
        return False


def _resolve_host_port(backend_key, host=None, port=None):
    """未指定 host/port 时从配置文件读取"""
    if host is not None and port is not None:
        return host, port
    config = load_llamacpp_config()
    cfg = config.get(backend_key, {})
    return (
        host or cfg.get("host", "127.0.0.1"),
        port or cfg.get("port", 11434),
    )


def list_llamacpp_models(host=None, port=None):
    """列出可用的 llama-server 模型"""
    host, port = _resolve_host_port("Llama.cpp", host, port)
    models = []
    try:
        response = httpx.get(f"http://{host}:{port}/v1/models", timeout=2.0)
        if response.status_code == 200:
            data = response.json()
            models = [m["id"] for m in data.get("data", [])]
    except (httpx.RequestError, httpx.HTTPStatusError):
        pass
    return models


def list_lmstudio_models(host=None, port=None):
    """列出 LM-Studio 可用模型"""
    host, port = _resolve_host_port("Lmstudio", host, port)
    models = []
    try:
        response = httpx.get(f"http://{host}:{port}/v1/models", timeout=2.0)
        if response.status_code == 200:
            data = response.json()
            models = [m["id"] for m in data.get("data", [])]
    except (httpx.RequestError, httpx.HTTPStatusError):
        pass
    return models


def _lmstudio_translate(text, target_lang, model_name, host=None, port=None):
    """通过 LM-Studio API 翻译"""
    host, port = _resolve_host_port("Lmstudio", host, port)
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


def _ollama_translate(text, target_lang, model_name, host=None, port=None):
    """通过 Ollama API 翻译"""
    host, port = _resolve_host_port("Ollama", host, port)
    tgt_code = LANGUAGES.get(target_lang, "zh")

    prompt = (
        f"You are a professional translator to {target_lang} ({tgt_code}).\n"
        f"Produce only the {target_lang} translation, no explanations.\n\n{text}"
    )

    response = httpx.post(
        f"http://{host}:{port}/api/chat",
        json={
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60.0,
    )
    response.raise_for_status()
    return response.json()["message"]["content"].strip()


def _llamacpp_translate(text, target_lang, model_name, host=None, port=None):
    """通过 llama-server HTTP API 翻译"""
    host, port = _resolve_host_port("Llama.cpp", host, port)
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
    host=None,
    port=None,
):
    def log(msg):
        if log_callback:
            log_callback(msg)

    if host is None or port is None:
        backend_key = {
            "ollama": "Ollama",
            "llamacpp": "Llama.cpp",
            "lmstudio": "Lmstudio",
        }.get(backend, "Ollama")
        host, port = _resolve_host_port(backend_key, host, port)

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
                translations[i] = _ollama_translate(
                    text, target_lang, model_name, host, port
                )
        except (OSError, RuntimeError, ValueError, httpx.RequestError) as e:
            log(f"第 {i + 1} 条翻译失败: {e}")
            translations[i] = text
        done_count += 1
        if progress_callback:
            progress_callback(done_count, total)

    indices = [i for i in range(total) if subs[i].content.strip()]
    with ThreadPoolExecutor(max_workers=batch_size) as executor:
        executor.map(translate_one, indices)

    originals = [sub.content.strip() for sub in subs]

    new_subs = []
    for i, sub in enumerate(subs):
        if translations[i]:
            sub.content = translations[i]
        new_subs.append(sub)

    if output_path is None:
        from pathlib import Path

        p = Path(srt_path)
        target_code = LANGUAGES.get(target_lang, target_lang)
        suffix = (
            f"_bilingual_{target_code}" if mode == "bilingual" else f"_{target_code}"
        )
        output_path = str(p.with_name(f"{p.stem}{suffix}{p.suffix}"))

    if mode == "bilingual":
        for i, sub in enumerate(new_subs):
            orig = originals[i]
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
