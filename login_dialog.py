import sys
from PyQt5.QtWidgets import (
    QDialog, QFrame, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor
from db import connect_to_db

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔒 Вход в систему")
        self.setFixedSize(400, 260)

        # Карточка входа
        card = QFrame(self)
        card.setObjectName("loginCard")
        card.setFixedSize(360, 220)

        # Layout внутри карточки
        v = QVBoxLayout(card)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(8)

        title = QLabel("Пожалуйста, войдите", card)
        title.setObjectName("loginTitle")
        title.setAlignment(Qt.AlignCenter)
        v.addWidget(title)

        # Поле логина
        self.edit_user = QLineEdit(card)
        self.edit_user.setPlaceholderText("Логин")
        v.addWidget(self.edit_user)

        # Поле пароля
        self.edit_pass = QLineEdit(card)
        self.edit_pass.setEchoMode(QLineEdit.Password)
        self.edit_pass.setPlaceholderText("Пароль")
        v.addWidget(self.edit_pass)

        # Кнопка
        btn = QPushButton("Войти", card)
        btn.setObjectName("loginBtn")
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn.clicked.connect(self.check_credentials)
        v.addWidget(btn)

        # Центрируем карточку в диалоге
        outer = QHBoxLayout(self)
        outer.addStretch()
        outer.addWidget(card)
        outer.addStretch()

    def check_credentials(self):
        user = self.edit_user.text().strip()
        pw   = self.edit_pass.text().strip()
        conn = connect_to_db()
        if not conn:
            QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к БД")
            return

        cur = conn.cursor()
        cur.execute(
            "SELECT ID, Store, Surname_N_LN FROM DITE_Logins WHERE Login=? AND Password=?",
            (user, pw)
        )
        row = cur.fetchone()
        conn.close()

        if row:
            self.user_id  = row.ID
            self.store    = row.Store
            self.fullname = row.Surname_N_LN
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Применяем стиль
    try:
        with open("style.qss", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        pass

    dlg = LoginDialog()
    if dlg.exec_() == QDialog.Accepted:
        print("Успешный вход:", dlg.fullname)
    sys.exit(0)
