import sys
import os
import json
from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLineEdit, QToolBar, QTabWidget,
    QFileDialog, QMessageBox, QListWidget, QDialog,
    QVBoxLayout, QStyleFactory
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QIcon, QFontDatabase

DATA_FILE = "browser_data.json"

# ---------------- Download Manager ----------------
class DownloadManager(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Downloads")
        self.resize(400, 300)
        self.list = QListWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.list)
        self.setLayout(layout)

    def add(self, text):
        self.list.addItem(text)

# ---------------- Browser ----------------
class WayangBrowser(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Wayang Browser")
        self.resize(1400, 900)

        # ---------------- App Icon ----------------
        if os.path.exists("wayang_app_icon.png"):
            self.setWindowIcon(QIcon("wayang_app_icon.png"))

        # ---------------- Data ----------------
        self.data = self.load_data()
        self.downloads = DownloadManager()

        # ---------------- Tabs ----------------
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.sync_url)
        self.tabs.setIconSize(QtCore.QSize(12, 12))  # kleiner Favicon
        self.setCentralWidget(self.tabs)

        # ---------------- Toolbar ----------------
        self.create_toolbar()

        # ---------------- Fonts ----------------
        if os.path.exists("Roboto-Regular.ttf"):
            QFontDatabase.addApplicationFont("Roboto-Regular.ttf")
            self.font_family = "Roboto"
        else:
            self.font_family = None

        # ---------------- Theme ----------------
        self.dark_mode = True
        self.apply_styles()

        # ---------------- First Tab ----------------
        self.new_tab(QUrl("https://www.google.com"))

    # ---------------- Styles ----------------
    def apply_styles(self):
        if self.dark_mode:
            bg_tab = "#1e1e1e"
            bg_tab_selected = "#2a2a2a"
            tab_hover = "#333"
            text_tab = "#aaa"
            text_selected = "white"
            toolbar_bg = "#1e1e1e"
            lineedit_bg = "#2a2a2a"
            lineedit_text = "white"
            main_bg = "#121212"
        else:
            bg_tab = "#ddd"
            bg_tab_selected = "#fff"
            tab_hover = "#eee"
            text_tab = "#555"
            text_selected = "#000"
            toolbar_bg = "#ccc"
            lineedit_bg = "#fff"
            lineedit_text = "#000"
            main_bg = "#f5f5f5"

        font_family_css = f'font-family: "{self.font_family}";' if self.font_family else ""

        # Main window and toolbar
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {main_bg}; }}

            QToolBar {{
                background: {toolbar_bg};
                spacing: 8px;
                padding: 6px;
                border: none;
            }}

            QToolButton {{
                background: transparent;
                color: {text_selected};
                padding: 6px;
                border-radius: 6px;
                font-family: "Roboto";
                font-size: 11pt;
            }}

            QToolButton:hover {{ background: {tab_hover}; }}

            QLineEdit {{
                background: {lineedit_bg};
                color: {lineedit_text};
                border-radius: 10px;
                padding: 6px 12px;
                border: 1px solid #3a3a3a;
                min-width: 420px;
                font-family: "{self.font_family}" if self.font_family else "";
                font-size: 11pt;
            }}

            QTabBar::tab {{
                background: {bg_tab};
                color: {text_tab};
                padding: 8px 14px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-left: 2px;
                margin-right: 2px;
                font-size: 8pt;
            }}
            QTabBar::tab:selected {{
                background: {bg_tab_selected};
                color: {text_selected};
                font-size: 8pt;
            }}
            QTabBar::tab:hover {{
                background: {tab_hover};
                color: {text_selected};
            }}
            QTabBar::close-button {{
                subcontrol-position: right;
                width: 12px;
                height: 12px;
            }}
            QTabBar::close-button:hover {{
                background: #ff5555;
            }}
        """)

    # ---------------- Toolbar ----------------
    def create_toolbar(self):
        tb = QToolBar()
        self.addToolBar(tb)

        tb.addAction(QIcon.fromTheme("go-previous"), "Zurück", lambda: self.current().back())
        tb.addAction(QIcon.fromTheme("go-next"), "Vor", lambda: self.current().forward())
        tb.addAction(QIcon.fromTheme("view-refresh"), "Neu laden", lambda: self.current().reload())
        tb.addAction(QIcon.fromTheme("go-home"), "Home", self.home)

        self.url = QLineEdit()
        self.url.returnPressed.connect(self.navigate)
        tb.addWidget(self.url)

        tb.addAction(QIcon.fromTheme("tab-new"), "Neuer Tab", self.new_tab)
        tb.addAction(QIcon.fromTheme("bookmark-new"), "Lesezeichen", self.add_bookmark)
        tb.addAction(QIcon.fromTheme("view-list-details"), "Downloads", self.downloads.show)
        tb.addAction(QIcon.fromTheme("view-private"), "Inkognito", self.new_incognito_tab)
        tb.addAction("🌗 Light/Dark", self.toggle_dark_mode)

    # ---------------- Tabs ----------------
    def new_tab(self, url=None):
        browser = QWebEngineView()
        browser.setUrl(url or QUrl("https://www.google.com"))

        i = self.tabs.addTab(browser, "Neuer Tab")
        self.tabs.setCurrentIndex(i)

        browser.urlChanged.connect(lambda u: self.update_url(u))
        browser.titleChanged.connect(lambda t: self.tabs.setTabText(i, t[:18]))
        browser.urlChanged.connect(lambda u: self.add_history(u.toString()))
        browser.page().profile().downloadRequested.connect(self.handle_download)

        if os.path.exists("wayang_favicon.png"):
            self.tabs.setTabIcon(i, QIcon("wayang_favicon.png"))

    def new_incognito_tab(self):
        browser = QWebEngineView()
        profile = browser.page().profile()
        profile.setPersistentCookiesPolicy(profile.NoPersistentCookies)
        browser.setUrl(QUrl("https://www.google.com"))
        i = self.tabs.addTab(browser, "Inkognito")
        self.tabs.setCurrentIndex(i)
        if os.path.exists("wayang_favicon.png"):
            self.tabs.setTabIcon(i, QIcon("wayang_favicon.png"))

    def close_tab(self, index):
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)

    def current(self):
        return self.tabs.currentWidget()

    # ---------------- Navigation ----------------
    def navigate(self):
        text = self.url.text()
        if text.startswith("http"):
            url = QUrl(text)
        elif "." in text:
            url = QUrl("https://" + text)
        else:
            url = QUrl(f"https://www.google.com/search?q={text}")
        self.current().setUrl(url)

    def update_url(self, url):
        self.url.setText(url.toString())

    def sync_url(self):
        self.update_url(self.current().url())

    def home(self):
        self.current().setUrl(QUrl("https://www.google.com"))

    # ---------------- Bookmarks ----------------
    def add_bookmark(self):
        try:
            self.data["bookmarks"].append({
                "title": self.current().title(),
                "url": self.current().url().toString()
            })
            self.save_data()
            QMessageBox.information(self, "Lesezeichen", "Gespeichert")
        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"Lesezeichen konnte nicht gespeichert werden:\n{e}")

    # ---------------- History ----------------
    def add_history(self, url):
        try:
            self.data["history"].append(url)
            self.save_data()
        except:
            pass

    # ---------------- Downloads ----------------
    def handle_download(self, download):
        path, _ = QFileDialog.getSaveFileName(self, "Download", download.path())
        if path:
            download.setPath(path)
            download.accept()
            self.downloads.add(path)

    # ---------------- Storage ----------------
    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {"bookmarks": [], "history": []}
        return {"bookmarks": [], "history": []}

    def save_data(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except:
            pass

    # ---------------- Toggle Light/Dark ----------------
    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.apply_styles()

# ---------------- Main ----------------
if __name__ == "__main__":
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-software-rasterizer"
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    browser = WayangBrowser()
    browser.show()
    sys.exit(app.exec_())
