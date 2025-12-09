# dashboard.py
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QSizePolicy, QMessageBox
)
from PyQt5.QtCore import Qt
from db import get_connection
from book import BooksWindow
from members import MembersWindow
from authors import AuthorsWindow
from club import ClubWindow
from loan import LoanWindow

ROLE_NAMES = {1: "ADMIN", 2: "LIBRARIAN", 3: "MEMBER"}

class DashboardWindow(QMainWindow):
    def __init__(self, username, role_id):
        super().__init__()
        self.setWindowTitle("LIMKOKWING UNIVERSITY'S CENTRAL LIBRARY")
        self.setGeometry(160, 80, 1000, 620)
        self.username = username
        self.role_id = role_id
        self.role = ROLE_NAMES.get(role_id, "MEMBER")

        # child windows refs
        self.child_windows = {}

        main = QWidget()
        main_layout = QVBoxLayout()
        main.setLayout(main_layout)

        # top bar
        top = QFrame()
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel(f"<b>Welcome Back, {username} ({self.role})</b>"))
        top_layout.addStretch()

        # Logout button (always visible)
        self.logout_btn = QPushButton("Logout")
        self.logout_btn.clicked.connect(self.logout)
        top_layout.addWidget(self.logout_btn)

        # Settings button - only enabled for Admin
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(self.open_settings)
        top_layout.addWidget(self.settings_btn)

        if self.role != "ADMIN":
            self.settings_btn.setEnabled(False)

        top.setLayout(top_layout)
        main_layout.addWidget(top)

        # summary grid
        self.summary_grid = QGridLayout()
        main_layout.addLayout(self.summary_grid)
        self.load_summary()

        # feature buttons (top row)
        btn_row = QHBoxLayout()
        # Books accessible to all (but buttons inside windows will be controlled)
        self.books_btn = QPushButton("Books")
        self.books_btn.clicked.connect(lambda: self.open_window("books", BooksWindow))
        btn_row.addWidget(self.books_btn)

        self.authors_btn = QPushButton("Authors")
        self.authors_btn.clicked.connect(lambda: self.open_window("authors", AuthorsWindow))
        btn_row.addWidget(self.authors_btn)

        self.members_btn = QPushButton("Members")
        self.members_btn.clicked.connect(lambda: self.open_window("members", MembersWindow))
        btn_row.addWidget(self.members_btn)

        self.clubs_btn = QPushButton("Book Clubs")
        self.clubs_btn.clicked.connect(lambda: self.open_window("clubs", ClubWindow))
        btn_row.addWidget(self.clubs_btn)

        self.loans_btn = QPushButton("Loans")
        self.loans_btn.clicked.connect(lambda: self.open_window("loans", LoanWindow))
        btn_row.addWidget(self.loans_btn)

        main_layout.addLayout(btn_row)
        main_layout.addStretch()
        self.setCentralWidget(main)

        # initial role-based UI adjustments
        self.apply_role_restrictions()

    def apply_role_restrictions(self):
        # Admin can view & delete & settings but cannot add/loan -> we will control inside child windows
        # Librarian can do everything except system settings
        # Member can only view
        # Here we only disable access to member management for members
        if self.role == "MEMBER":
            self.members_btn.setEnabled(False)
            self.clubs_btn.setEnabled(False)

    def load_summary(self):
        # clear existing widgets in grid
        while self.summary_grid.count():
            item = self.summary_grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        conn = get_connection()
        if not conn:
            return
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM books"); total_books = cur.fetchone()[0] or 0
        cur.execute("SELECT SUM(available_copies) FROM books"); available = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM loan WHERE status = 'LOANED'"); borrowed = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM loan WHERE status = 'OVERDUE'"); overdue = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM authors"); total_authors = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM members"); total_members = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM book_clubs"); total_clubs = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM users"); total_users = cur.fetchone()[0] or 0
        cur.close(); conn.close()

        cards = [
            ("Total Books", total_books),
            ("Available", available),
            ("Borrowed", borrowed),
            ("Overdue", overdue),
            ("Authors", total_authors),
            ("Members", total_members),
            ("Clubs", total_clubs),
            ("Users", total_users)
        ]

        for i, (label, value) in enumerate(cards):
            frame = QFrame()
            frame.setMinimumSize(160, 100)
            layout = QVBoxLayout()
            layout.addStretch()
            layout.addWidget(QLabel(f"<h2>{value}</h2>", ))
            layout.addWidget(QLabel(label))
            layout.addStretch()
            frame.setLayout(layout)
            self.summary_grid.addWidget(frame, i//4, i%4)

    def open_settings(self):
        # for demo: simple dialog that lets admin run a refresh or view schema info
        if self.role != "ADMIN":
            QMessageBox.warning(self, "Access denied", "Settings are for Admin only.")
            return
        QMessageBox.information(self, "Settings", "Admin can change system settings here (demo).")

    def open_window(self, key, WindowClass):
        # Reuse window instance if already open, pass role so window can enable/disable controls
        if key in self.child_windows and self.child_windows[key] is not None:
            w = self.child_windows[key]
        else:
            # instantiate with role info so child windows can check permissions
            w = WindowClass(role=self.role)
            # if window has a data_changed signal, connect it to refresh dashboard counters
            try:
                w.data_changed.connect(self.on_data_changed)
            except Exception:
                pass
            self.child_windows[key] = w
        w.show()
        w.raise_()

    def on_data_changed(self):
        # child window tells us data changed -> refresh summary
        self.load_summary()

    def logout(self):
        # close all child windows
        for k, w in list(self.child_windows.items()):
            if w:
                try:
                    w.close()
                except Exception:
                    pass
                self.child_windows[k] = None
        # show login window
        from login import LoginWindow
        self.close()
        self.login = LoginWindow()
        self.login.show()
