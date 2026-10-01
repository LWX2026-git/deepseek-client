# -*- coding: utf-8 -*-
"""
DeepSeek Client（单文件三合一 · v8 稳定版）

v8 修复：
  ★ DEBUG_MODE = False → 去掉控制台黑窗
  ★ 圆角 12px → 22px → 更圆润
  ★ 按钮/卡片圆角相应加大
  ★ 图标三处强化：Nuitka / App / Window 都用同一 ico

保留 v7 全部功能：
  - WebEngine 在 QApplication 之前准备
  - Cookies 三处持久化补丁
  - 日志到 %TEMP%
  - Nuitka 失败显示完整输出
  - 图标缺失直接报错
  - Inno {localappdata} + WorkingDir
  - --include-qt-plugins=all
"""
import os
import sys
import shutil
import subprocess
import traceback
import tempfile
import datetime


# =========================================================
# ★ 全局保险：WebEngine 必须在 QApplication 之前准备
# =========================================================
try:
    from PyQt6.QtCore import Qt as _Qt, QCoreApplication as _QCoreApp
    _QCoreApp.setAttribute(
        _Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)
    from PyQt6.QtWebEngineWidgets import QWebEngineView  # noqa
    from PyQt6.QtWebEngineCore import (                   # noqa
        QWebEngineProfile, QWebEnginePage,
        QWebEngineDownloadRequest, QWebEngineSettings
    )
    _WEBENGINE_READY = True
except ImportError:
    _WEBENGINE_READY = False


def _bootstrap_log():
    try:
        log_dir = os.path.join(tempfile.gettempdir(), "DeepSeekClient")
        os.makedirs(log_dir, exist_ok=True)
        p = os.path.join(log_dir, "boot.log")
        with open(p, "a", encoding="utf-8") as f:
            f.write(f"\n{'=' * 60}\n")
            f.write(f"[{datetime.datetime.now()}] 进程启动\n")
            f.write(f"  argv       = {sys.argv}\n")
            f.write(f"  cwd        = {os.getcwd()}\n")
            f.write(f"  executable = {sys.executable}\n")
            f.write(f"  frozen     = {getattr(sys, 'frozen', False)}\n")
        return p
    except Exception:
        return None


_BOOT_LOG = _bootstrap_log()


APP_NAME = "DeepSeekClient"
EXE_NAME = "DeepSeekClient.exe"
SETUP_NAME = "DeepSeekClient_Setup"
APP_TITLE = "DeepSeek Client"
APP_VERSION = "1.0.0"
APP_URL = "https://chat.deepseek.com"
APP_ID = "DeepSeekClient"

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
BUILD_ROOT = os.path.join(PROJECT_DIR, "ds_exe")
BUILD_DIR = os.path.join(BUILD_ROOT, "build")
DIST_DIR = os.path.join(BUILD_DIR, "main.dist")
ICON_PATH = os.path.join(BUILD_ROOT, "icon.ico")
ISS_PATH = os.path.join(BUILD_DIR, "installer.iss")

_LOG_DIR = os.path.join(tempfile.gettempdir(), "DeepSeekClient")
try:
    os.makedirs(_LOG_DIR, exist_ok=True)
except Exception:
    _LOG_DIR = os.path.join(os.path.expanduser("~"), ".deepseek_client")
    os.makedirs(_LOG_DIR, exist_ok=True)

CLIENT_LOG = os.path.join(_LOG_DIR, "client_error.log")
BUILD_LOG = os.path.join(_LOG_DIR, "build_error.log")

MAIN_SCRIPT = os.path.abspath(__file__)

CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0

# ★★★ v8：发布模式，去掉控制台黑窗 ★★★
DEBUG_MODE = False

# ---- 配色 ----
BG = "#1e1e1e"
CARD = "#252525"
CARD2 = "#2d2d2d"
BORDER = "#3c3c3c"
TEXT = "#e0e0e0"
SUB = "#888888"
ACCENT = "#4D6BFE"
ACCENT2 = "#7aa2f7"
DANGER = "#e81123"

W, H = 1200, 800
# ★★★ v8：窗口圆角半径（像素），值越大越圆润 ★★★
WINDOW_RADIUS = 22


def is_compiled():
    return ("__compiled__" in globals()
            or getattr(sys, "frozen", False)
            or getattr(sys, "nuitka_compiled", False))


def _log(msg):
    try:
        with open(CLIENT_LOG, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass
    try:
        print(msg)
    except Exception:
        pass


# =========================================================
#  客户端
# =========================================================
def run_client():
    _log("=" * 60)
    _log(f"[Client] 进程启动 pid={os.getpid()}")
    _log(f"[Client] executable={sys.executable}")
    _log(f"[Client] cwd={os.getcwd()}")
    _log(f"[Client] webengine_ready={_WEBENGINE_READY}")
    try:
        _run_client_impl()
    except SystemExit:
        raise
    except BaseException as e:
        tb = traceback.format_exc()
        _log("=" * 60)
        _log("客户端启动失败")
        _log("=" * 60)
        _log(tb)
        try:
            from PyQt6.QtWidgets import QApplication, QMessageBox
            _app = QApplication.instance() or QApplication([])
            QMessageBox.critical(
                None, "客户端启动失败",
                f"{e}\n\n详细日志：\n{CLIENT_LOG}")
        except Exception:
            pass
        sys.exit(1)


def _run_client_impl():
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
        "--disable-gpu "
        "--no-sandbox "
        "--disable-software-rasterizer "
        "--disable-features=RendererCodeIntegrity "
        "--disable-dev-shm-usage "
        "--single-process"
    )
    os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"

    _log("[Client] 开始启动")
    if not _WEBENGINE_READY:
        raise RuntimeError(
            "PyQt6 WebEngine 未就绪，请先安装：\n"
            "pip install PyQt6 PyQt6-WebEngine")

    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QIcon
    from PyQt6.QtCore import QStandardPaths, QTimer

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("DeepSeek")

    # ★★★ v8：应用级图标（任务栏也生效）★★★
    if os.path.exists(ICON_PATH):
        app.setWindowIcon(QIcon(ICON_PATH))
        _log(f"[Client] App 图标已设置: {ICON_PATH}")
    else:
        _log(f"[Client] 警告：找不到 {ICON_PATH}")

    _log("[Client] QApplication 已创建")

    from PyQt6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QProgressBar, QFileDialog,
        QScrollArea, QFrame
    )
    from PyQt6.QtCore import Qt, QUrl
    from PyQt6.QtGui import QPainter, QPainterPath, QColor

    app_data_dir = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.AppLocalDataLocation)
    if not app_data_dir:
        base = os.getenv("LOCALAPPDATA") or os.path.expanduser("~")
        app_data_dir = os.path.join(base, APP_NAME)
    os.makedirs(app_data_dir, exist_ok=True)

    storage_dir = os.path.join(app_data_dir, "storage")
    cache_dir = os.path.join(app_data_dir, "cache")
    os.makedirs(storage_dir, exist_ok=True)
    os.makedirs(cache_dir, exist_ok=True)
    _log(f"[Client] 数据目录: {app_data_dir}")

    profile = QWebEngineProfile(APP_NAME, None)
    profile.setPersistentStoragePath(storage_dir)
    profile.setCachePath(cache_dir)
    profile.setPersistentCookiesPolicy(
        QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
    profile.setHttpCacheType(
        QWebEngineProfile.HttpCacheType.DiskHttpCache)
    try:
        profile.setPersistentPermissionsPolicy(
            QWebEngineProfile.PersistentPermissionsPolicy.StoreOnDisk)
    except AttributeError:
        pass

    profile.setHttpUserAgent(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
    _log("[Client] Profile 配置完成")

    try:
        profile.cookieStore().loadAllCookies()
        _log("[Client] 已加载磁盘 Cookies")
    except Exception as e:
        _log(f"[Client] loadAllCookies 失败: {e}")

    _flush_timer = QTimer()
    _flush_timer.setInterval(30 * 1000)
    def _flush_cookies():
        try:
            profile.cookieStore().flushCookies()
        except Exception:
            pass
    _flush_timer.timeout.connect(_flush_cookies)
    _flush_timer.start()

    # ★★★ v8：QSS 圆角同步加大 ★★★
    QSS = f"""
    QMainWindow, QWidget#centralWidget {{ background-color: {BG}; color: {TEXT}; }}
    QLabel {{ color: {TEXT}; background: transparent; }}
    QPushButton {{
        background-color: {CARD2}; color: {TEXT};
        border: 1px solid {BORDER}; border-radius: 9px;
        padding: 5px 14px; font-size: 13px;
    }}
    QPushButton:hover {{ background-color: {BORDER}; border-color: #505050; }}
    QPushButton#closeBtn:hover {{
        background-color: {DANGER}; color: white; border-color: {DANGER};
    }}
    QProgressBar {{
        background-color: {CARD2}; border: 1px solid {BORDER};
        border-radius: 5px; text-align: center; color: {TEXT};
        font-size: 11px; max-height: 16px;
    }}
    QProgressBar::chunk {{ background-color: {ACCENT}; border-radius: 4px; }}
    QScrollArea {{ border: none; background-color: {BG}; }}
    QScrollBar:vertical {{ background: {BG}; width: 8px; border-radius: 4px; }}
    QScrollBar::handle:vertical {{
        background: #424242; border-radius: 4px; min-height: 30px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QFrame#titleBar {{
        background-color: {CARD};
        border-top-left-radius: {WINDOW_RADIUS}px;
        border-top-right-radius: {WINDOW_RADIUS}px;
        border-bottom: 1px solid {BORDER};
    }}
    QFrame#downloadPanel {{
        background-color: {CARD}; border-top: 1px solid {BORDER};
        border-bottom-left-radius: {WINDOW_RADIUS}px;
        border-bottom-right-radius: {WINDOW_RADIUS}px;
    }}
    QFrame#downloadItem {{
        background-color: {CARD2}; border: 1px solid {BORDER};
        border-radius: 10px;
    }}
    """

    class DownloadItemWidget(QFrame):
        def __init__(self, download, parent=None):
            super().__init__(parent)
            self.download = download
            self.setObjectName("downloadItem")
            self.setFixedHeight(60)

            layout = QHBoxLayout(self)
            layout.setContentsMargins(10, 6, 10, 6)
            layout.setSpacing(8)

            self.name_label = QLabel(download.downloadFileName())
            self.name_label.setStyleSheet("font-size: 13px; font-weight: bold;")
            self.name_label.setFixedWidth(280)

            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setFixedWidth(200)

            self.status_label = QLabel("等待中...")
            self.status_label.setStyleSheet(f"font-size: 11px; color: {SUB};")
            self.status_label.setFixedWidth(130)

            self.open_btn = QPushButton("打开")
            self.open_btn.setFixedWidth(50)
            self.open_btn.clicked.connect(self._open_file)
            self.open_btn.setEnabled(False)

            self.folder_btn = QPushButton("文件夹")
            self.folder_btn.setFixedWidth(60)
            self.folder_btn.clicked.connect(self._open_folder)
            self.folder_btn.setEnabled(False)

            self.cancel_btn = QPushButton("取消")
            self.cancel_btn.setFixedWidth(50)
            self.cancel_btn.clicked.connect(download.cancel)

            layout.addWidget(self.name_label)
            layout.addWidget(self.progress_bar)
            layout.addWidget(self.status_label)
            layout.addWidget(self.open_btn)
            layout.addWidget(self.folder_btn)
            layout.addWidget(self.cancel_btn)

            download.receivedBytesChanged.connect(self._on_received)
            download.totalBytesChanged.connect(self._on_total)
            download.stateChanged.connect(self._on_state)

        def _on_received(self, received):
            total = self.download.totalBytes()
            if total > 0:
                self.progress_bar.setValue(int(received / total * 100))
                self.status_label.setText(
                    f"{self._fmt(received)} / {self._fmt(total)}")
            else:
                self.progress_bar.setRange(0, 0)
                self.status_label.setText(self._fmt(received))

        def _on_total(self, total):
            self.progress_bar.setRange(0, 100 if total > 0 else 0)

        def _on_state(self, state):
            S = QWebEngineDownloadRequest.DownloadState
            if state == S.DownloadCompleted:
                self.progress_bar.setValue(100)
                self.status_label.setText("✅ 已完成")
                self.cancel_btn.setEnabled(False)
                self.open_btn.setEnabled(True)
                self.folder_btn.setEnabled(True)
            elif state == S.DownloadCancelled:
                self.status_label.setText("❌ 已取消")
                self.cancel_btn.setEnabled(False)
            elif state == S.DownloadInterrupted:
                self.status_label.setText("⚠️ 中断")
                self.cancel_btn.setEnabled(False)
            elif state == S.DownloadPaused:
                self.status_label.setText("⏸ 已暂停")
            elif state == S.DownloadInProgress:
                self.status_label.setText("⬇ 下载中...")

        def _open_file(self):
            p = os.path.join(self.download.downloadDirectory(),
                             self.download.downloadFileName())
            if os.path.exists(p):
                os.startfile(p)

        def _open_folder(self):
            p = self.download.downloadDirectory()
            if os.path.exists(p):
                os.startfile(p)

        @staticmethod
        def _fmt(b):
            if b < 1024:
                return f"{b} B"
            if b < 1024 * 1024:
                return f"{b / 1024:.1f} KB"
            if b < 1024 * 1024 * 1024:
                return f"{b / (1024 * 1024):.1f} MB"
            return f"{b / (1024 * 1024 * 1024):.2f} GB"

    class DownloadPanel(QFrame):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setObjectName("downloadPanel")
            self.setFixedHeight(200)

            layout = QVBoxLayout(self)
            layout.setContentsMargins(10, 8, 10, 8)
            layout.setSpacing(6)

            header = QHBoxLayout()
            title = QLabel("📥 下载管理")
            title.setStyleSheet("font-size: 14px; font-weight: bold;")
            close_btn = QPushButton("✕")
            close_btn.setObjectName("closeBtn")
            close_btn.setFixedSize(28, 28)
            close_btn.clicked.connect(lambda: self.setVisible(False))
            header.addWidget(title)
            header.addStretch()
            header.addWidget(close_btn)
            layout.addLayout(header)

            self.scroll = QScrollArea()
            self.scroll.setWidgetResizable(True)
            self.scroll.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.list_widget = QWidget()
            self.list_layout = QVBoxLayout(self.list_widget)
            self.list_layout.setContentsMargins(0, 0, 0, 0)
            self.list_layout.setSpacing(6)
            self.list_layout.addStretch()
            self.scroll.setWidget(self.list_widget)
            layout.addWidget(self.scroll)

        def add_download(self, download):
            item = DownloadItemWidget(download, self)
            self.list_layout.insertWidget(self.list_layout.count() - 1, item)

    class DeepSeekClient(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle(APP_TITLE)
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
            self.setAttribute(
                Qt.WidgetAttribute.WA_TranslucentBackground, True)
            self.resize(W, H)
            self.setMinimumSize(800, 600)
            self._drag_pos = None
            self.setStyleSheet(QSS)

            # ★★★ v8：窗口图标（标题栏 / 任务栏）★★★
            if os.path.exists(ICON_PATH):
                self.setWindowIcon(QIcon(ICON_PATH))
                _log(f"[Client] 窗口图标已设置")

            self._build_ui()
            profile.downloadRequested.connect(self._on_download)

        def _build_ui(self):
            central = QWidget()
            central.setObjectName("centralWidget")
            self.setCentralWidget(central)

            root = QVBoxLayout(central)
            root.setContentsMargins(0, 0, 0, 0)
            root.setSpacing(0)

            self.title_bar = QFrame()
            self.title_bar.setObjectName("titleBar")
            self.title_bar.setFixedHeight(42)
            tb = QHBoxLayout(self.title_bar)
            tb.setContentsMargins(14, 0, 8, 0)
            tb.setSpacing(6)

            title = QLabel("🐳 DeepSeek")
            title.setStyleSheet(
                f"font-size: 14px; font-weight: bold; color: {TEXT};")

            self.refresh_btn = QPushButton("刷新")
            self.refresh_btn.setFixedSize(56, 28)
            self.refresh_btn.setToolTip("刷新页面 (F5)")
            self.refresh_btn.clicked.connect(lambda: self.browser.reload())

            self.dl_toggle = QPushButton("📥")
            self.dl_toggle.setFixedSize(32, 28)
            self.dl_toggle.setToolTip("下载管理")
            self.dl_toggle.clicked.connect(self._toggle_dl_panel)

            min_btn = QPushButton("─")
            min_btn.setFixedSize(32, 28)
            min_btn.clicked.connect(self.showMinimized)

            max_btn = QPushButton("□")
            max_btn.setFixedSize(32, 28)
            max_btn.clicked.connect(
                lambda: self.showNormal() if self.isMaximized()
                else self.showMaximized())

            close_btn = QPushButton("✕")
            close_btn.setObjectName("closeBtn")
            close_btn.setFixedSize(32, 28)
            close_btn.clicked.connect(self.close)

            tb.addWidget(title)
            tb.addStretch()
            tb.addWidget(self.refresh_btn)
            tb.addWidget(self.dl_toggle)
            tb.addWidget(min_btn)
            tb.addWidget(max_btn)
            tb.addWidget(close_btn)
            root.addWidget(self.title_bar)

            self.browser = QWebEngineView()
            page = QWebEnginePage(profile, self.browser)
            self.browser.setPage(page)

            try:
                self.browser.settings().setAttribute(
                    QWebEngineSettings.WebAttribute.ForceDarkMode, True)
            except AttributeError:
                pass

            self.browser.setUrl(QUrl(APP_URL))
            root.addWidget(self.browser, stretch=1)

            self.dl_panel = DownloadPanel(self)
            self.dl_panel.setVisible(False)
            root.addWidget(self.dl_panel)

        def _on_download(self, download):
            default_name = download.downloadFileName()
            save_path, _ = QFileDialog.getSaveFileName(
                self, "保存文件", default_name, "所有文件 (*.*)")
            if not save_path:
                download.cancel()
                return
            download.setDownloadDirectory(os.path.dirname(save_path))
            download.setDownloadFileName(os.path.basename(save_path))
            download.accept()
            self.dl_panel.add_download(download)
            if not self.dl_panel.isVisible():
                self.dl_panel.setVisible(True)

        def _toggle_dl_panel(self):
            self.dl_panel.setVisible(not self.dl_panel.isVisible())

        def mousePressEvent(self, e):
            if e.button() == Qt.MouseButton.LeftButton and \
                    self.title_bar.geometry().contains(e.pos()):
                self._drag_pos = (e.globalPosition().toPoint()
                                  - self.frameGeometry().topLeft())
                e.accept()

        def mouseMoveEvent(self, e):
            if self._drag_pos is not None and \
                    e.buttons() & Qt.MouseButton.LeftButton:
                self.move(e.globalPosition().toPoint() - self._drag_pos)
                e.accept()

        def mouseReleaseEvent(self, e):
            self._drag_pos = None
            e.accept()

        def keyPressEvent(self, e):
            if e.key() == Qt.Key.Key_F5:
                self.browser.reload()
            else:
                super().keyPressEvent(e)

        # ★★★ v8：paintEvent 圆角同步加大 ★★★
        def paintEvent(self, event):
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            rounded = QPainterPath()
            rounded.addRoundedRect(
                0, 0, self.width(), self.height(),
                WINDOW_RADIUS, WINDOW_RADIUS)
            p.setClipPath(rounded)
            p.fillPath(rounded, QColor(BG))
            super().paintEvent(event)

    if os.path.exists(ICON_PATH):
        app.setWindowIcon(QIcon(ICON_PATH))

    _log("[Client] 创建主窗口")
    win = DeepSeekClient()
    win.show()
    _log("[Client] 窗口已显示")

    def _cleanup():
        try:
            profile.cookieStore().flushCookies()
        except Exception:
            pass
        try:
            _flush_timer.stop()
        except Exception:
            pass
        try:
            profile.deleteLater()
        except Exception:
            pass
    app.aboutToQuit.connect(_cleanup)

    sys.exit(app.exec())


# =========================================================
#  构建器
# =========================================================
def run_builder():
    try:
        import PyQt6  # noqa
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install",
                               "PyQt6", "PyQt6-WebEngine",
                               "-q", "--disable-pip-version-check"])

    from PyQt6.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
        QPushButton, QProgressBar, QTextEdit, QMessageBox
    )
    from PyQt6.QtCore import QThread, pyqtSignal

    class BuildWorker(QThread):
        progress = pyqtSignal(int)
        status = pyqtSignal(str)
        log = pyqtSignal(str)
        done = pyqtSignal(bool, str)

        def __init__(self, skip_nuitka=False):
            super().__init__()
            self.skip_nuitka = skip_nuitka
            self.dist = None
            self.setup = None

        def _run(self, cmd, cwd=None, label=""):
            if label:
                self.log.emit(f"\n>>> {label}")
            self.log.emit(f"$ {' '.join(cmd)}")
            p = subprocess.Popen(
                cmd, cwd=cwd, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, bufsize=1,
                encoding="utf-8", errors="ignore",
                creationflags=CREATE_NO_WINDOW)

            collected = []
            for line in p.stdout:
                line = line.rstrip()
                if line:
                    self.log.emit(line)
                    collected.append(line)

            p.wait()
            if p.returncode != 0:
                tail = "\n".join(collected[-80:])
                raise RuntimeError(
                    f"{label} 失败 exit {p.returncode}\n\n"
                    f"=== 最后 80 行输出 ===\n{tail}"
                )

        def run(self):
            try:
                os.makedirs(BUILD_ROOT, exist_ok=True)
                os.makedirs(BUILD_DIR, exist_ok=True)

                self.status.emit("检查依赖 ...")
                if not self.skip_nuitka:
                    for mod, pkg in {"nuitka": "nuitka"}.items():
                        try:
                            __import__(mod)
                        except ImportError:
                            self._run([sys.executable, "-m", "pip", "install",
                                       pkg, "-q",
                                       "--disable-pip-version-check"])
                self.progress.emit(10)

                if not os.path.exists(ICON_PATH):
                    raise RuntimeError(
                        f"找不到图标文件：\n{ICON_PATH}\n\n"
                        f"请把 icon.ico 放到 ds_exe 目录下再重新构建。")
                self.log.emit(f"[图标] 使用 {ICON_PATH}")
                self.progress.emit(15)

                if self.skip_nuitka:
                    self.status.emit("跳过 Nuitka，使用已有编译结果")
                    self.log.emit("[跳过] Nuitka 编译")
                    self.progress.emit(85)
                else:
                    self.status.emit("Nuitka 编译中 ...（目录模式）")
                    self._nuitka()
                    self.progress.emit(85)

                self.status.emit("整理输出 ...")
                self.dist = self._find_dist()
                if not self.dist:
                    raise RuntimeError("找不到 main.dist 目录")
                self.log.emit(f"[独立目录] {self.dist}")
                self.progress.emit(90)

                self.status.emit("生成安装程序 ...")
                self._installer()
                self.progress.emit(100)

                if self.setup and os.path.exists(self.setup):
                    self.done.emit(True, self.setup)
                else:
                    self.done.emit(True,
                                   os.path.join(self.dist, EXE_NAME))
            except Exception as e:
                self.log.emit(f"\n[!] {e}")
                self.log.emit(traceback.format_exc())
                self.done.emit(False, str(e))

        def _nuitka(self):
            # ★★★ v8：DEBUG_MODE=False → console_mode="disable" ★★★
            console_mode = "force" if DEBUG_MODE else "disable"
            cmd = [
                sys.executable, "-m", "nuitka",
                "--standalone",
                f"--windows-console-mode={console_mode}",
                "--enable-plugin=pyqt6",
                "--msvc=latest",
                "--assume-yes-for-downloads",
                "--remove-output",
                "--lto=no",
                "--python-flag=no_docstrings",
                "--python-flag=no_asserts",
                "--nofollow-import-to=pytest,unittest,test,setuptools,"
                                     "pip,wheel,tkinter.test,lib2to3",
                "--include-package=PyQt6",
                "--include-package=PyQt6.QtCore",
                "--include-package=PyQt6.QtGui",
                "--include-package=PyQt6.QtWidgets",
                "--include-package=PyQt6.QtNetwork",
                "--include-package=PyQt6.QtWebChannel",
                "--include-package=PyQt6.QtWebEngineCore",
                "--include-package=PyQt6.QtWebEngineWidgets",
                "--include-package=PyQt6.QtWebEngineQuick",
                "--include-qt-plugins=all",
                f"--output-dir={BUILD_DIR}",
                f"--output-filename={EXE_NAME}",
                "--company-name=DeepSeek",
                "--product-name=DeepSeek Client",
                f"--file-version={APP_VERSION}.0",
                f"--product-version={APP_VERSION}.0",
            ]
            # ★★★ v8：exe 内嵌图标 ★★★
            cmd.append(f"--windows-icon-from-ico={ICON_PATH}")
            cmd.append(MAIN_SCRIPT)
            self._run(cmd, cwd=PROJECT_DIR, label="Nuitka")

        def _find_dist(self):
            if os.path.isdir(DIST_DIR) and \
                    os.path.exists(os.path.join(DIST_DIR, EXE_NAME)):
                return DIST_DIR
            for n in os.listdir(BUILD_DIR):
                f = os.path.join(BUILD_DIR, n)
                if os.path.isdir(f) and n.endswith(".dist") and \
                        os.path.exists(os.path.join(f, EXE_NAME)):
                    return f
            return None

        def _installer(self):
            iscc = None
            for c in [r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
                      r"C:\Program Files\Inno Setup 6\ISCC.exe"]:
                if os.path.exists(c):
                    iscc = c
                    break
            if not iscc:
                self.log.emit("[!] 未找到 Inno Setup，跳过安装包生成")
                return

            icon_line = f"SetupIconFile={ICON_PATH}"

            content = f'''[Setup]
AppName={APP_TITLE}
AppVersion={APP_VERSION}
AppPublisher=DeepSeek
AppId={APP_ID}
DefaultDirName={{localappdata}}\\Programs\\{APP_TITLE}
DefaultGroupName={APP_TITLE}
UninstallDisplayIcon={{app}}\\{EXE_NAME}
OutputDir={BUILD_ROOT}
OutputBaseFilename={SETUP_NAME}
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes
WizardStyle=modern
{icon_line}
ArchitecturesInstallIn64BitMode=x64
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
MinVersion=10.0
SetupLogging=yes
UsePreviousAppDir=yes
UsePreviousGroup=yes
Uninstallable=yes
AllowNoIcons=yes

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务:"; Flags: checkedonce

[Files]
Source: "{self.dist}\\*"; DestDir: "{{app}}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{{autodesktop}}\\{APP_TITLE}"; Filename: "{{app}}\\{EXE_NAME}"; WorkingDir: "{{app}}"; Tasks: desktopicon
Name: "{{group}}\\{APP_TITLE}";         Filename: "{{app}}\\{EXE_NAME}"; WorkingDir: "{{app}}"
Name: "{{group}}\\卸载 {APP_TITLE}";    Filename: "{{uninstallexe}}"

[Run]
Filename: "{{app}}\\{EXE_NAME}"; WorkingDir: "{{app}}"; Description: "启动 {APP_TITLE}"; Flags: postinstall nowait skipifsilent
'''
            with open(ISS_PATH, "w", encoding="utf-8-sig") as f:
                f.write(content)
            self._run([iscc, ISS_PATH], cwd=BUILD_DIR, label="Inno Setup")
            self.setup = os.path.join(BUILD_ROOT, f"{SETUP_NAME}.exe")

    class BuildWindow(QWidget):
        def __init__(self, skip_nuitka=False):
            super().__init__()
            self.setWindowTitle(f"{APP_TITLE} · 构建")
            self.setFixedSize(760, 560)
            self.setStyleSheet(f"""
                QWidget {{ background: {BG}; color: {TEXT};
                          font-family: "Microsoft YaHei"; }}
                QProgressBar {{ background: {CARD};
                    border: 1px solid {BORDER}; border-radius: 8px;
                    height: 20px; text-align: center;
                    color: {TEXT}; font-weight: bold; }}
                QProgressBar::chunk {{ background: {ACCENT};
                                      border-radius: 7px; }}
                QTextEdit {{ background: {CARD}; color: {TEXT};
                    border: 1px solid {BORDER}; border-radius: 10px;
                    font-family: Consolas, monospace; font-size: 11px;
                    padding: 8px; }}
                QPushButton {{ background: {ACCENT}; color: #111;
                    border: none; border-radius: 10px;
                    padding: 10px 24px; font-size: 13px;
                    font-weight: bold; }}
                QPushButton:hover {{ background: {ACCENT2}; }}
                QPushButton:disabled {{ background: {BORDER};
                                       color: {SUB}; }}
            """)

            lay = QVBoxLayout(self)
            lay.setContentsMargins(20, 20, 20, 20)
            lay.setSpacing(12)

            t = QLabel(f"🐳 {APP_TITLE} · 自动构建")
            t.setStyleSheet(f"color: {ACCENT}; font-size: 20px;"
                            f"font-weight: bold;")
            lay.addWidget(t)

            mode = ("仅 Inno Setup 打包" if skip_nuitka
                    else "Nuitka 目录模式 + Inno Setup")
            debug_note = " · 调试模式" if DEBUG_MODE else " · 发布模式"
            info = QLabel(f"模式：{mode}{debug_note} · 输出：{BUILD_ROOT}")
            info.setStyleSheet(f"color: {SUB}; font-size: 11px;")
            lay.addWidget(info)

            self.status = QLabel("准备中 ...")
            self.status.setStyleSheet(f"color: {TEXT}; font-size: 13px;"
                                      f"font-weight: bold;")
            lay.addWidget(self.status)

            self.bar = QProgressBar()
            self.bar.setRange(0, 100)
            lay.addWidget(self.bar)

            self.log = QTextEdit()
            self.log.setReadOnly(True)
            lay.addWidget(self.log, 1)

            br = QHBoxLayout()
            br.addStretch()

            self.open_btn = QPushButton("📂 打开输出目录")
            self.open_btn.setEnabled(False)
            self.open_btn.clicked.connect(lambda: os.startfile(BUILD_ROOT))
            br.addWidget(self.open_btn)

            self.launch_btn = QPushButton("▶ 启动程序")
            self.launch_btn.setEnabled(False)
            self.launch_btn.clicked.connect(self._launch)
            br.addWidget(self.launch_btn)
            lay.addLayout(br)

            self.exe_path = None
            self.worker = BuildWorker(skip_nuitka=skip_nuitka)
            self.worker.progress.connect(self.bar.setValue)
            self.worker.status.connect(self.status.setText)
            self.worker.log.connect(self._append_log)
            self.worker.done.connect(self._done)
            self.worker.start()

        def _append_log(self, s):
            self.log.append(s)
            self.log.verticalScrollBar().setValue(
                self.log.verticalScrollBar().maximum())

        def _done(self, ok, msg):
            if ok:
                self.exe_path = msg
                self.status.setText("✅ 构建完成")
                self.launch_btn.setEnabled(True)
                self.open_btn.setEnabled(True)
                QMessageBox.information(self, "成功", f"构建完成：\n{msg}")
            else:
                self.status.setText("❌ 构建失败")
                try:
                    with open(BUILD_LOG, "w", encoding="utf-8") as f:
                        f.write(f"[{datetime.datetime.now()}]\n")
                        f.write(msg)
                        f.write("\n\n=== 完整日志 ===\n")
                        f.write(self.log.toPlainText())
                except Exception:
                    pass
                QMessageBox.critical(
                    self, "失败",
                    f"{msg}\n\n完整日志已写入：\n{BUILD_LOG}")

        def _launch(self):
            if self.exe_path and os.path.exists(self.exe_path):
                subprocess.Popen(
                    [self.exe_path],
                    cwd=os.path.dirname(self.exe_path),
                    creationflags=CREATE_NO_WINDOW)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME + " Build")

    existing_exe = os.path.join(DIST_DIR, EXE_NAME)
    skip_nuitka = False
    if os.path.exists(existing_exe):
        msg = QMessageBox()
        msg.setWindowTitle("检测到已有编译结果")
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setText("检测到已编译的程序")
        msg.setInformativeText(
            f"路径：\n{existing_exe}\n\n"
            f"是否直接使用该结果生成安装程序？\n\n"
            f"• 是：跳过 Nuitka 编译，直接 Inno Setup 打包（速度快）\n"
            f"• 否：完整重新编译（源码有改动时选这个）\n"
            f"• 取消：退出构建器"
        )
        btn_yes = msg.addButton("是（直接打包）", QMessageBox.ButtonRole.YesRole)
        btn_no = msg.addButton("否（重新编译）", QMessageBox.ButtonRole.NoRole)
        msg.addButton("取消", QMessageBox.ButtonRole.RejectRole)
        msg.setDefaultButton(btn_no)
        msg.exec()

        clicked = msg.clickedButton()
        if clicked is btn_yes:
            skip_nuitka = True
        elif clicked is btn_no:
            skip_nuitka = False
        else:
            sys.exit(0)

    win = BuildWindow(skip_nuitka=skip_nuitka)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    argv = sys.argv[1:]

    if "--client" in argv or "--run" in argv:
        run_client()
    elif "--build" in argv:
        run_builder()
    elif is_compiled():
        run_client()
    else:
        run_builder()