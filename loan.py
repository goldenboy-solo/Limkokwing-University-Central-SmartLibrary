# loan.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton,
    QHBoxLayout, QFormLayout, QLineEdit, QMessageBox
)
from PyQt5.QtCore import pyqtSignal
from db import get_connection

class LoanWindow(QWidget):
    data_changed = pyqtSignal()

    def __init__(self, role="MEMBER"):
        super().__init__()
        self.role = role
        self.setWindowTitle("Loans Management")
        self.setGeometry(260, 160, 860, 520)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("<b>Loans - Issue & Return</b>"))

        h = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh Loans"); self.refresh_btn.clicked.connect(self.load_loans)
        h.addWidget(self.refresh_btn); layout.addLayout(h)

        self.table = QTableWidget(); layout.addWidget(self.table)

        form = QFormLayout()
        self.input_book_id = QLineEdit(); self.input_member_id = QLineEdit()
        self.issue_btn = QPushButton("Issue Book"); self.issue_btn.clicked.connect(self.issue_book)
        form.addRow("Book ID:", self.input_book_id); form.addRow("Member ID:", self.input_member_id); form.addRow(self.issue_btn)
        layout.addLayout(form)

        rform = QFormLayout()
        self.input_loan_id = QLineEdit(); self.return_btn = QPushButton("Return Book (by Loan ID)"); self.return_btn.clicked.connect(self.return_book)
        rform.addRow("Loan ID to return:", self.input_loan_id); rform.addRow(self.return_btn)
        layout.addLayout(rform)

        self.setLayout(layout)
        self.apply_permissions()
        self.load_loans()

    def apply_permissions(self):
        if self.role == "ADMIN":
            # admin cannot issue or return per spec (admin only view & delete)
            self.issue_btn.setEnabled(False); self.return_btn.setEnabled(False)
        elif self.role == "LIBRARIAN":
            self.issue_btn.setEnabled(True); self.return_btn.setEnabled(True)
        else:
            self.issue_btn.setEnabled(False); self.return_btn.setEnabled(False)

    def warn_conn(self):
        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "DB Error", "Cannot connect to database.")
        return conn

    def load_loans(self):
        conn = self.warn_conn(); 
        if not conn: return
        cur = conn.cursor()
        cur.execute("""
            SELECT l.loan_id, b.book_id, b.title, m.member_id, m.full_name, l.loan_date, l.due_date, l.return_date, l.status
            FROM loan l
            JOIN books b ON l.book_id = b.book_id
            JOIN members m ON l.member_id = m.member_id
            ORDER BY l.loan_id
        """)
        rows = cur.fetchall()
        cur.close(); conn.close()
        self.table.setRowCount(len(rows)); self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(["LoanID","BookID","Book Title","MemberID","Member","Loan Date","Due Date","Return Date","Status"])
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(val) if val is not None else ""))

    def issue_book(self):
        if self.role != "LIBRARIAN":
            QMessageBox.warning(self, "Permission denied", "Only librarians can issue books."); return
        book_id = self.input_book_id.text().strip(); member_id = self.input_member_id.text().strip()
        if not book_id or not member_id:
            QMessageBox.warning(self, "Input Error", "Book ID and Member ID are required."); return
        conn = self.warn_conn(); 
        if not conn: return
        cur = conn.cursor()
        try:
            cur.execute("SELECT available_copies FROM books WHERE book_id = %s", (int(book_id),))
            r = cur.fetchone()
            if not r: QMessageBox.warning(self, "Error", "Book not found."); cur.close(); conn.close(); return
            if r[0] <= 0: QMessageBox.warning(self, "Not Available", "No copies available."); cur.close(); conn.close(); return
            cur.execute("SELECT COUNT(*) FROM loan WHERE member_id = %s AND status = 'LOANED'", (int(member_id),))
            cnt = cur.fetchone()[0]
            if cnt >= 3: QMessageBox.warning(self, "Limit Reached", "Member already has 3 active loans."); cur.close(); conn.close(); return
            cur.execute("BEGIN;")
            cur.execute("INSERT INTO loan (book_id, member_id, due_date, status) VALUES (%s,%s,CURRENT_DATE + INTERVAL '7 days','LOANED') RETURNING loan_id", (int(book_id), int(member_id)))
            loan_id = cur.fetchone()[0]
            cur.execute("UPDATE books SET available_copies = available_copies - 1 WHERE book_id = %s", (int(book_id),))
            cur.execute("COMMIT;")
            QMessageBox.information(self, "Success", f"Loan created (Loan ID: {loan_id}).")
            cur.close(); conn.close()
            self.data_changed.emit(); self.load_loans()
        except Exception as e:
            cur.execute("ROLLBACK;")
            cur.close(); conn.close()
            QMessageBox.critical(self, "DB Error", f"Failed to issue book: {e}")

    def return_book(self):
        if self.role != "LIBRARIAN":
            QMessageBox.warning(self, "Permission denied", "Only librarians can return books."); return
        loan_id = self.input_loan_id.text().strip()
        if not loan_id:
            QMessageBox.warning(self, "Input Error", "Loan ID required."); return
        conn = self.warn_conn(); 
        if not conn: return
        cur = conn.cursor()
        try:
            cur.execute("SELECT book_id, status FROM loan WHERE loan_id = %s", (int(loan_id),))
            r = cur.fetchone()
            if not r: QMessageBox.warning(self, "Error", "Loan not found."); cur.close(); conn.close(); return
            book_id, status = r
            if status == 'RETURNED': QMessageBox.information(self, "Info", "Loan already returned."); cur.close(); conn.close(); return
            cur.execute("BEGIN;")
            cur.execute("UPDATE loan SET status = 'RETURNED', return_date = NOW() WHERE loan_id = %s", (int(loan_id),))
            cur.execute("UPDATE books SET available_copies = available_copies + 1 WHERE book_id = %s", (int(book_id),))
            cur.execute("COMMIT;")
            QMessageBox.information(self, "Success", "Book returned successfully.")
            cur.close(); conn.close()
            self.data_changed.emit(); self.load_loans()
        except Exception as e:
            cur.execute("ROLLBACK;")
            cur.close(); conn.close()
            QMessageBox.critical(self, "DB Error", f"Failed to return book: {e}")
