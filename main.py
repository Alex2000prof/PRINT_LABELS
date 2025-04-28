# main.py

import sys
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QTabWidget, QVBoxLayout, QWidget
from PyQt5.QtGui import QIcon

from login_dialog    import LoginDialog
from task_dialog     import TaskDialog
from template_editor import TemplateEditor
from template_viewer import TemplateViewer
from basic_print_widget import BasicPrintWidget as PrintWidget
from updater         import check_for_update

import sys, os

def resource_path(rel_path: str) -> str:
    """
    Возвращает абсолютный путь к ресурсу.
    В режиме PyInstaller-packed (frozen) — внутри sys._MEIPASS,
    иначе — рядом со скриптом.
    """
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, rel_path)





class MainWindow(QMainWindow):
    def __init__(self, task_id, store_id, is_admin, user_id, fullname):
        super().__init__()

        self.setWindowTitle("Label Printer")
        self.setWindowIcon(QIcon(resource_path("icons/logo.png")))  # if logo.png is in an icons subfolder
        self.setGeometry(100, 100, 1000, 700)

        layout = QVBoxLayout()
        tabs = QTabWidget()

        # Передаем в PrintWidget все нужные параметры
        tabs.addTab(
            PrintWidget(task_id, store_id, user_id, fullname),
            'Печать'
        )

        if is_admin:
            tabs.addTab(TemplateEditor(), 'Редактор шаблона')

        layout.addWidget(tabs)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName("Label Printer")
    icon = QIcon(resource_path("icons/logo.png"))
    app.setWindowIcon(icon)

    # Загружаем style.qss
    qss_path = "style.qss"
    if not os.path.isfile(qss_path):
        # когда упаковано PyInstaller, ищем внутри _MEIPASS
        qss_path = resource_path("style.qss")
    try:
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except Exception as e:
        print("Не удалось загрузить QSS:", e)

    # Проверяем обновления в фоне
    check_for_update()

    # Логин
    login = LoginDialog()
    if login.exec_() != QDialog.Accepted:
        sys.exit(0)

    # Определяем, админ ли
    is_admin = (
        getattr(login, 'username', '') == 'Aleksander' and
        getattr(login, 'password', '') == '17391739'
    )
    store_id = login.store
    user_id  = login.user_id
    fullname = login.fullname

    # Выбор ТЗ
    task_dlg = TaskDialog(store_id)
    if task_dlg.exec_() != QDialog.Accepted:
        sys.exit(0)
    task_id = task_dlg.selected

    # Запускаем главное окно
    window = MainWindow(task_id, store_id, is_admin, user_id, fullname)
    window.show()

    sys.exit(app.exec_())




