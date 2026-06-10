import os
import sys
from pathlib import Path

import httpx
from backend import (
    LANGUAGES,
    list_ollama_models,
    list_llamacpp_models,
    list_lmstudio_models,
    translate_srt_file,
    start_llama_server,
    stop_llama_server,
    load_llamacpp_config,
    save_llamacpp_config,
)
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)


class LlamaCppConfigDialog(QDialog):
    """配置对话框"""

    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.setWindowTitle("配置")
        self.setMinimumWidth(500)
        self.config = config or load_llamacpp_config()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # llamacpp 配置组
        llamacpp_group = QGroupBox("llamacpp 配置")
        llamacpp_layout = QFormLayout()

        self.edit_executable = QLineEdit(self.config.get("executable", ""))
        self.edit_executable.setPlaceholderText("llama-server 可执行文件路径")
        btn_browse_exe = QPushButton("浏览")
        btn_browse_exe.clicked.connect(self._browse_executable)
        exe_layout = QHBoxLayout()
        exe_layout.addWidget(self.edit_executable)
        exe_layout.addWidget(btn_browse_exe)
        llamacpp_layout.addRow("可执行文件:", exe_layout)

        self.edit_model_dir = QLineEdit(self.config.get("model_dir", ""))
        self.edit_model_dir.setPlaceholderText("模型文件目录")
        btn_browse_dir = QPushButton("浏览")
        btn_browse_dir.clicked.connect(self._browse_model_dir)
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.edit_model_dir)
        dir_layout.addWidget(btn_browse_dir)
        llamacpp_layout.addRow("模型目录:", dir_layout)

        self.spin_port = QSpinBox()
        self.spin_port.setRange(1024, 65535)
        self.spin_port.setValue(self.config.get("port", 11433))
        llamacpp_layout.addRow("端口号:", self.spin_port)

        self.edit_host = QLineEdit(self.config.get("host", "127.0.0.1"))
        self.edit_host.setPlaceholderText("服务器 IP")
        llamacpp_layout.addRow("IP 地址:", self.edit_host)

        self.spin_gpu_layers = QSpinBox()
        self.spin_gpu_layers.setRange(0, 1000)
        self.spin_gpu_layers.setValue(self.config.get("n_gpu_layers", 30))
        llamacpp_layout.addRow("GPU 层数:", self.spin_gpu_layers)

        self.spin_ctx_size = QSpinBox()
        self.spin_ctx_size.setRange(512, 131072)
        self.spin_ctx_size.setSingleStep(1024)
        self.spin_ctx_size.setValue(self.config.get("ctx_size", 4096))
        llamacpp_layout.addRow("上下文窗口:", self.spin_ctx_size)

        llamacpp_group.setLayout(llamacpp_layout)
        layout.addWidget(llamacpp_group)

        # LM-Studio 配置组
        lmstudio_group = QGroupBox("LM-Studio 配置")
        lmstudio_layout = QFormLayout()

        self.spin_lmstudio_port = QSpinBox()
        self.spin_lmstudio_port.setRange(1024, 65535)
        self.spin_lmstudio_port.setValue(self.config.get("lmstudio_port", 1234))
        lmstudio_layout.addRow("端口号:", self.spin_lmstudio_port)

        self.edit_lmstudio_host = QLineEdit(self.config.get("lmstudio_host", "127.0.0.1"))
        self.edit_lmstudio_host.setPlaceholderText("服务器 IP")
        lmstudio_layout.addRow("IP 地址:", self.edit_lmstudio_host)

        lmstudio_group.setLayout(lmstudio_layout)
        layout.addWidget(lmstudio_group)

        btn_layout = QHBoxLayout()
        btn_save = QPushButton("保存")
        btn_save.clicked.connect(self._save)
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def _browse_executable(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 llama-server 可执行文件"
        )
        if path:
            self.edit_executable.setText(path)

    def _browse_model_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择模型目录")
        if path:
            self.edit_model_dir.setText(path)

    def _save(self):
        self.config = {
            "executable": self.edit_executable.text().strip(),
            "model_dir": self.edit_model_dir.text().strip(),
            "port": self.spin_port.value(),
            "n_gpu_layers": self.spin_gpu_layers.value(),
            "ctx_size": self.spin_ctx_size.value(),
            "lmstudio_port": self.spin_lmstudio_port.value(),
            "host": self.edit_host.text().strip() or "127.0.0.1",
            "lmstudio_host": self.edit_lmstudio_host.text().strip() or "127.0.0.1",
        }
        if not self.config["executable"]:
            QMessageBox.warning(self, "提示", "请填写可执行文件路径")
            return
        if not self.config["model_dir"]:
            QMessageBox.warning(self, "提示", "请填写模型目录")
            return
        save_llamacpp_config(self.config)
        self.accept()

    def get_config(self):
        return self.config


class TranslationWorker(QThread):
    progress = Signal(int, int)
    log_msg = Signal(str)
    finished = Signal(str)

    def __init__(
        self,
        files,
        target_lang,
        model_name,
        batch_size,
        mode,
        reverse,
        output_dir,
        backend="ollama",
        host="127.0.0.1",
        port=11433,
        config=None,
    ):
        super().__init__()
        self.files = files
        self.target_lang = target_lang
        self.model_name = model_name
        self.batch_size = batch_size
        self.mode = mode
        self.reverse = reverse
        self.output_dir = output_dir
        self.backend = backend
        self.host = host
        self.port = port
        self.config = config or {}
        self._is_running = True

    def run(self):
        total = len(self.files)
        self.log_msg.emit(f"共 {total} 个文件，开始翻译...")

        if self.backend == "llamacpp":
            self.log_msg.emit("正在启动 llama-server...")
            config = self.config
            host = config.get("host", "127.0.0.1")
            if not start_llama_server(
                self.model_name,
                model_dir=config.get("model_dir", "/mnt/D/llama/models"),
                host=host,
                port=config.get("port", 11433),
                n_gpu_layers=config.get("n_gpu_layers", 30),
                ctx_size=config.get("ctx_size", 4096),
                executable=config.get("executable", "/mnt/D/llama/llama-server"),
            ):
                self.log_msg.emit("启动 llama-server 失败，翻译中止。")
                self.finished.emit("failed")
                return
            self.log_msg.emit("llama-server 已就绪。")
        elif self.backend == "lmstudio":
            config = self.config
            host = config.get("lmstudio_host", "127.0.0.1")
            port = config.get("lmstudio_port", 1234)
            try:
                response = httpx.get(f"http://{host}:{port}/v1/models", timeout=2.0)
                if response.status_code != 200:
                    self.log_msg.emit("无法连接到 LM-Studio，请确保 LM-Studio 已启动。")
                    self.finished.emit("failed")
                    return
            except (httpx.RequestError, httpx.HTTPStatusError):
                self.log_msg.emit("无法连接到 LM-Studio，请确保 LM-Studio 已启动。")
                self.finished.emit("failed")
                return
            self.log_msg.emit("LM-Studio 已就绪。")

        try:
            for idx, file_path in enumerate(self.files):
                if not self._is_running:
                    break

                fname = os.path.basename(file_path)
                out_name = Path(fname).stem
                target_code = LANGUAGES.get(self.target_lang, self.target_lang)
                if self.mode == "bilingual":
                    out_name = f"{out_name}_bilingual_{target_code}.srt"
                else:
                    out_name = f"{out_name}_{target_code}.srt"
                out_path = os.path.join(self.output_dir, out_name)

                self.log_msg.emit(f"[{idx + 1}/{total}] {fname} -> {out_name}")
                self.progress.emit(idx, total)

                def prog(current, total_count):
                    self.progress.emit(current, total_count)

                def log_cb(msg):
                    self.log_msg.emit(f"  {msg}")

                try:
                    config = self.config
                    host = config.get("host", "127.0.0.1") if self.backend == "llamacpp" else config.get("lmstudio_host", "127.0.0.1")
                    port = config.get("port", 11433) if self.backend == "llamacpp" else config.get("lmstudio_port", 1234)
                    translate_srt_file(
                        srt_path=file_path,
                        target_lang=self.target_lang,
                        model_name=self.model_name,
                        batch_size=self.batch_size,
                        mode=self.mode,
                        reverse=self.reverse,
                        output_path=out_path,
                        progress_callback=prog,
                        log_callback=log_cb,
                        backend=self.backend,
                        host=host,
                        port=port,
                    )
                except (OSError, RuntimeError, ValueError) as e:
                    self.log_msg.emit(f"翻译失败 {fname}: {e}")
        finally:
            if self.backend == "llamacpp":
                self.log_msg.emit("正在停止 llama-server...")
                stop_llama_server()
                self.log_msg.emit("llama-server 已停止。")

        self.progress.emit(total, total)
        self.log_msg.emit("全部完成。")
        self.finished.emit("done")

    def stop(self):
        self._is_running = False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SRT 字幕翻译工具")
        self.setMinimumSize(820, 640)
        self._selected_files = []

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # ── 文件选择 ──
        file_group = QGroupBox("文件来源")
        file_layout = QHBoxLayout()

        self.input_path = QLineEdit()
        self.input_path.setPlaceholderText("选择一个或多个 SRT 文件...")
        self.btn_browse = QPushButton("浏览")
        self.btn_browse.clicked.connect(self._browse_input)
        file_layout.addWidget(self.input_path)
        file_layout.addWidget(self.btn_browse)

        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # ── 输出目录 ──
        out_group = QGroupBox("输出目录")
        out_layout = QHBoxLayout()

        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("选择输出文件夹...")
        self.btn_browse_out = QPushButton("浏览")
        self.btn_browse_out.clicked.connect(self._browse_output)
        out_layout.addWidget(self.output_path)
        out_layout.addWidget(self.btn_browse_out)

        out_group.setLayout(out_layout)
        layout.addWidget(out_group)

        # ── 翻译设置 ──
        settings_group = QGroupBox("翻译设置")
        settings_layout = QFormLayout()

        # 第一行：翻译方向 + 语言 + 输出模式
        row1_layout = QHBoxLayout()

        dir_label_layout = QVBoxLayout()
        dir_label_layout.addWidget(QLabel("翻译方向:"))
        radio_layout = QHBoxLayout()
        self.radio_zh2other = QRadioButton("中译多")
        self.radio_other2zh = QRadioButton("多译中")
        self.radio_other2zh.setChecked(True)
        radio_layout.addWidget(self.radio_zh2other)
        radio_layout.addWidget(self.radio_other2zh)
        dir_label_layout.addLayout(radio_layout)
        row1_layout.addLayout(dir_label_layout)

        self.lbl_lang = QLabel("源语言:")
        lang_label_layout = QVBoxLayout()
        lang_label_layout.addWidget(self.lbl_lang)
        self.combo_lang = QComboBox()
        other_langs = [l for l in LANGUAGES if l != "简体中文"]
        self.combo_lang.addItems(other_langs)
        lang_label_layout.addWidget(self.combo_lang)
        row1_layout.addLayout(lang_label_layout)

        out_mode_layout = QVBoxLayout()
        out_mode_layout.addWidget(QLabel("输出模式:"))
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["仅译文", "双语 (译文在上)", "双语 (原文在上)"])
        out_mode_layout.addWidget(self.combo_mode)
        row1_layout.addLayout(out_mode_layout)

        self.radio_zh2other.toggled.connect(self._on_direction_changed)

        settings_layout.addRow(row1_layout)

        # 第二行：并发数 + 后端选择 + 模型
        mode_layout = QHBoxLayout()

        batch_layout = QVBoxLayout()
        batch_layout.addWidget(QLabel("并发数:"))
        self.spin_batch = QSpinBox()
        self.spin_batch.setRange(1, 20)
        self.spin_batch.setValue(4)
        batch_layout.addWidget(self.spin_batch)
        mode_layout.addLayout(batch_layout)

        backend_layout = QVBoxLayout()
        backend_layout.addWidget(QLabel("后端:"))
        self.combo_backend = QComboBox()
        self.combo_backend.addItems(["ollama", "llamacpp", "lmstudio"])
        self.combo_backend.currentTextChanged.connect(self._on_backend_changed)
        backend_layout.addWidget(self.combo_backend)
        mode_layout.addLayout(backend_layout)

        model_label_layout = QVBoxLayout()
        model_label_layout.addWidget(QLabel("模型:"))
        self.combo_model = QComboBox()
        self.combo_model.setEditable(True)
        self.combo_model.setMinimumWidth(200)
        model_label_layout.addWidget(self.combo_model)
        mode_layout.addLayout(model_label_layout)

        settings_layout.addRow(mode_layout)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # ── 操作按钮 ──
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("开始翻译")
        self.btn_start.setFixedHeight(42)
        self.btn_start.setStyleSheet(
            "font-weight: bold; font-size: 14px; background-color: #4CAF50; color: white;",
        )
        self.btn_start.clicked.connect(self._start)

        self.btn_stop = QPushButton("停止")
        self.btn_stop.setFixedHeight(42)
        self.btn_stop.setStyleSheet(
            "font-weight: bold; font-size: 14px; background-color: #f44336; color: white;",
        )
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop)

        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)
        layout.addLayout(btn_layout)

        # ── 进度 & 日志 ──
        progress_group = QGroupBox("进度")
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        progress_layout.addWidget(self.log_output)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # ── 初始化 ──
        self.worker = None
        self._fetch_models()

    def _fetch_models(self):
        self.combo_model.clear()
        backend = self.combo_backend.currentText()
        
        if backend == "ollama":
            models = list_ollama_models()
            if models:
                self.combo_model.addItems(models)
                self.log(f"已加载 {len(models)} 个 Ollama 模型。")
            else:
                self.combo_model.addItems(["translategemma:27b", "translategemma:12b", "translategemma:4b"])
                self.log("未检测到 Ollama，使用默认模型列表。")
        elif backend == "llamacpp":
            config = load_llamacpp_config()
            models = list_llamacpp_models(
                port=config.get("port", 11433),
                model_dir=config.get("model_dir", "/mnt/D/llama/models"),
            )
            if models:
                self.combo_model.addItems(models)
                self.log(f"已加载 {len(models)} 个可用模型。")
            else:
                self.combo_model.addItems(["Hy-MT2-1.8B-Q8_0"])
                self.log("未找到可用模型，使用默认模型列表。")
        elif backend == "lmstudio":
            config = load_llamacpp_config()
            host = config.get("lmstudio_host", "127.0.0.1")
            port = config.get("lmstudio_port", 1234)
            models = list_lmstudio_models(host=host, port=port)
            if models:
                self.combo_model.addItems(models)
                self.log(f"已加载 {len(models)} 个 LM-Studio 模型。")
            else:
                self.log("未检测到 LM-Studio 或无可用模型。")

    def _browse_input(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择字幕文件",
            filter="字幕文件 (*.srt);;所有文件 (*)",
        )
        if files:
            files = [f.replace(os.sep, "/") for f in files]
            self._selected_files = files
            if len(files) == 1:
                self.input_path.setText(files[0])
            else:
                self.input_path.setText(f"已选择 {len(files)} 个文件")
            if not self.output_path.text():
                parent = os.path.dirname(files[0])
                self.output_path.setText(
                    os.path.join(parent, "output").replace(os.sep, "/")
                )

    def _browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if folder:
            self.output_path.setText(folder.replace(os.sep, "/"))

    def _on_direction_changed(self, checked):
        if self.radio_zh2other.isChecked():
            self.lbl_lang.setText("目标语言:")
        else:
            self.lbl_lang.setText("源语言:")

    def _on_backend_changed(self, text):
        if text == "llamacpp":
            config = load_llamacpp_config()
            from backend import CONFIG_FILE
            if not CONFIG_FILE.exists():
                dialog = LlamaCppConfigDialog(self, config)
                if dialog.exec() != QDialog.Accepted:
                    self.combo_backend.setCurrentText("ollama")
                    return
        elif text == "lmstudio":
            from backend import CONFIG_FILE
            if not CONFIG_FILE.exists():
                config = load_llamacpp_config()
                dialog = LlamaCppConfigDialog(self, config)
                if dialog.exec() != QDialog.Accepted:
                    self.combo_backend.setCurrentText("ollama")
                    return
        self._fetch_models()

    def _check_lmstudio_connection(self, config=None):
        """检查 LM-Studio 连接"""
        if config is None:
            config = load_llamacpp_config()
        host = config.get("lmstudio_host", "127.0.0.1")
        port = config.get("lmstudio_port", 1234)
        try:
            response = httpx.get(f"http://{host}:{port}/v1/models", timeout=2.0)
            return response.status_code == 200
        except (httpx.RequestError, httpx.HTTPStatusError):
            return False

    def _log(self, msg):
        self.log_output.append(msg)
        sb = self.log_output.verticalScrollBar()
        sb.setValue(sb.maximum())

    def log(self, msg):
        self._log(msg)

    def _get_mode(self):
        idx = self.combo_mode.currentIndex()
        if idx == 0:
            return "translation", False
        elif idx == 1:
            return "bilingual", False
        else:
            return "bilingual", True

    def _collect_files(self):
        if self._selected_files:
            return [f for f in self._selected_files if os.path.isfile(f)]
        return []

    def _start(self):
        files = self._collect_files()
        if not files:
            self._log("错误: 未找到可翻译的 SRT 文件。")
            return

        output_dir = self.output_path.text().strip()
        if not output_dir:
            self._log("错误: 请选择输出目录。")
            return
        os.makedirs(output_dir, exist_ok=True)

        mode, reverse = self._get_mode()

        lang = self.combo_lang.currentText()
        if self.radio_zh2other.isChecked():
            target_lang = lang
        else:
            target_lang = "简体中文"

        model_name = self.combo_model.currentText()
        backend = self.combo_backend.currentText()
        
        config = load_llamacpp_config() if backend in ["llamacpp", "lmstudio"] else {}

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_start.setText("翻译中...")

        self.worker = TranslationWorker(
            files=files,
            target_lang=target_lang,
            model_name=model_name,
            batch_size=self.spin_batch.value(),
            mode=mode,
            reverse=reverse,
            output_dir=output_dir,
            backend=backend,
            config=config,
        )
        self.worker.log_msg.connect(self._log)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _stop(self):
        if self.worker:
            self.worker.stop()
            self._log("已停止翻译。")

    def _on_progress(self, current, total):
        self.progress_bar.setMaximum(max(total, 1))
        self.progress_bar.setValue(current)

    def _on_finished(self, result):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_start.setText("开始翻译")
        if result == "done":
            self._log("翻译任务完成。")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
