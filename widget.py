import sys
import os
import ctypes
from ctypes import wintypes
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, 
                               QSystemTrayIcon, QMenu, QListWidget, QListWidgetItem,
                               QFileIconProvider)
from PySide6.QtCore import Qt, QFileInfo, QSize, QSettings, QPoint
from PySide6.QtGui import QAction, QIcon, QPixmap, QPainter, QColor

class DraggableListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self._drag_pos = None
        self.setAcceptDrops(False)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton and not self.itemAt(event.pos()):
            self._drag_pos = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if self._drag_pos is not None:
            self.parent_window.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self._drag_pos is not None:
            self.parent_window.save_config()
        self._drag_pos = None

class FenceWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._is_quitting = False
        self.settings = QSettings("PyFencesOrg", "PyFencesApp")
        self.run_settings = QSettings("HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run", QSettings.Format.NativeFormat)
        self.app_reg_key = "PyFencesApp"
        
        self.init_ui()
        self.init_tray()
        self.load_config()

    def init_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAcceptDrops(True)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.list_widget = DraggableListWidget(self)
        self.list_widget.setViewMode(QListWidget.ViewMode.IconMode)
        self.list_widget.setIconSize(QSize(48, 48))
        self.list_widget.setSpacing(15)
        self.list_widget.setWordWrap(True)
        
        self.list_widget.setStyleSheet(
            "QListWidget { background-color: rgba(45, 45, 45, 160); border: none; color: white; outline: none; }"
            "QListWidget::item:selected { background-color: rgba(255, 255, 255, 40); border-radius: 4px; }"
        )
        
        self.list_widget.itemDoubleClicked.connect(self.open_item)
        self.layout.addWidget(self.list_widget)

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(55, 118, 171))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, 64, 64)
        painter.setPen(QColor(255, 232, 115))
        font = painter.font()
        font.setPixelSize(32)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "Py")
        painter.end()
        
        self.tray_icon.setIcon(QIcon(pixmap))
        
        self.tray_menu = QMenu()
        
        # 添加：显示组件菜单项
        show_action = QAction("显示组件", self)
        show_action.triggered.connect(self.show_widget)
        self.tray_menu.addAction(show_action)
        
        self.tray_menu.addSeparator()
        
        self.autostart_action = QAction("开机自动启动", self, checkable=True)
        self.autostart_action.setChecked(self.run_settings.contains(self.app_reg_key))
        self.autostart_action.toggled.connect(self.toggle_autostart)
        self.tray_menu.addAction(self.autostart_action)
        
        self.tray_menu.addSeparator()
        
        quit_action = QAction("退出程序", self)
        quit_action.triggered.connect(self.quit_app)
        self.tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(self.tray_menu)
        
        # 添加：绑定托盘激活事件（双击等）
        self.tray_icon.activated.connect(self.on_tray_activated)
        
        self.tray_icon.show()

    def on_tray_activated(self, reason):
        # 拦截双击事件
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_widget()

    def show_widget(self):
        # 清除可能被系统强加的最小化状态，并强制显示
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized)
        self.show()
        self.activateWindow()

    def quit_app(self):
        self._is_quitting = True
        QApplication.instance().quit()

    def toggle_autostart(self, checked):
        if checked:
            app_path = os.path.abspath(sys.argv[0])
            if app_path.lower().endswith('.py') or app_path.lower().endswith('.pyw'):
                python_exe = sys.executable
                exec_cmd = f'"{python_exe}" "{app_path}"'
            else:
                exec_cmd = f'"{app_path}"'
            self.run_settings.setValue(self.app_reg_key, exec_cmd)
        else:
            self.run_settings.remove(self.app_reg_key)

    def embed_to_desktop(self):
        user32 = ctypes.windll.user32
        progman = user32.FindWindowW("Progman", None)
        user32.SendMessageTimeoutW(progman, 0x052C, 0, 0, 0, 1000, None)
        
        self.workerw = 0
        def enum_windows(hwnd, lParam):
            if user32.FindWindowExW(hwnd, 0, "SHELLDLL_DefView", None):
                self.workerw = user32.FindWindowExW(0, hwnd, "WorkerW", None)
            return True
            
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(WNDENUMPROC(enum_windows), 0)
        
        if self.workerw:
            hwnd = int(self.winId())
            user32.SetParent(hwnd, self.workerw)
            
            if hasattr(user32, 'GetWindowLongPtrW'):
                GetWindowLong = user32.GetWindowLongPtrW
                SetWindowLong = user32.SetWindowLongPtrW
            else:
                GetWindowLong = user32.GetWindowLongW
                SetWindowLong = user32.SetWindowLongW
            
            GetWindowLong.argtypes = [wintypes.HWND, ctypes.c_int]
            GetWindowLong.restype = ctypes.c_void_p
            SetWindowLong.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]
            SetWindowLong.restype = ctypes.c_void_p
            
            GWL_STYLE = -16
            WS_CHILD = 0x40000000
            WS_POPUP = 0x80000000
            
            style = GetWindowLong(hwnd, GWL_STYLE)
            if style is not None:
                style = (style | WS_CHILD) & ~WS_POPUP
                SetWindowLong(hwnd, GWL_STYLE, style)

    def hideEvent(self, event):
        if getattr(self, '_is_quitting', False):
            event.accept()
        else:
            event.ignore()
            self.show()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def is_item_exists(self, path):
        for i in range(self.list_widget.count()):
            if self.list_widget.item(i).data(Qt.ItemDataRole.UserRole) == path:
                return True
        return False

    def dropEvent(self, event):
        provider = QFileIconProvider()
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            
            if self.is_item_exists(file_path):
                continue
                
            file_info = QFileInfo(file_path)
            icon = provider.icon(file_info)
            item = QListWidgetItem(icon, file_info.fileName())
            item.setData(Qt.ItemDataRole.UserRole, file_path)
            self.list_widget.addItem(item)
        event.accept()
        self.save_config()

    def open_item(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path and os.path.exists(path):
            os.startfile(path)

    def save_config(self):
        self.settings.setValue("pos", self.pos())
        self.settings.setValue("size", self.size())
        
        files = []
        for i in range(self.list_widget.count()):
            files.append(self.list_widget.item(i).data(Qt.ItemDataRole.UserRole))
        self.settings.setValue("files", files)

    def load_config(self):
        pos = self.settings.value("pos", QPoint(100, 100))
        size = self.settings.value("size", QSize(400, 300))
        self.resize(size)
        self.move(pos)
        
        files = self.settings.value("files", [])
        if files:
            provider = QFileIconProvider()
            for file_path in files:
                if os.path.exists(file_path):
                    file_info = QFileInfo(file_path)
                    icon = provider.icon(file_info)
                    item = QListWidgetItem(icon, file_info.fileName())
                    item.setData(Qt.ItemDataRole.UserRole, file_path)
                    self.list_widget.addItem(item)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FenceWidget()
    
    app.aboutToQuit.connect(window.save_config)
    
    window.show()
    window.embed_to_desktop()
    
    sys.exit(app.exec())