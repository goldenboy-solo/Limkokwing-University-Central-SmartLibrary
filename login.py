# login.py
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox
)
from db import get_connection, verify_password
from PyQt5.QtCore import Qt

ROLE_NAMES = {1: "ADMIN", 2: "LIBRARIAN", 3: "MEMBER"}

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SmartLibrary - Login")
        self.setGeometry(420, 180, 420, 220)
        layout = QVBoxLayout()
        layout.setSpacing(12)

        title = QLabel("<h2>SmartLibrary Login</h2>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Username
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Username:"))
        self.username_input = QLineEdit()
        h1.addWidget(self.username_input)
        layout.addLayout(h1)

        # Password
        h2 = QHBoxLayout()
        h2.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        h2.addWidget(self.password_input)
        layout.addLayout(h2)

        # Buttons
        btn_layout = QHBoxLayout()
        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.check_login)
        btn_layout.addStretch()
        btn_layout.addWidget(self.login_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def check_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Required", "Enter username and password")
            return

        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "DB Error", "Could not connect to database")
            return
        cur = conn.cursor()
        cur.execute("SELECT user_id, password_hash, role_id FROM users WHERE username = %s", (username,))
        row = cur.fetchone()
        cur.close(); conn.close()
        if not row:
            QMessageBox.warning(self, "Login Failed", "User not found")
            return

        user_id, password_hash, role_id = row
        if verify_password(password, password_hash):
            # import here to avoid circular imports at module load
            from dashboard import DashboardWindow
            self.hide()
            self.dashboard = DashboardWindow(username, role_id)
            # show dashboard and give it a reference to this login window so it can show it back on logout
            self.dashboard.login_window = self
            self.dashboard.show()
        else:
            QMessageBox.warning(self, "Login Failed", "Incorrect password")