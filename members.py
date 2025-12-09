# members.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton,
    QHBoxLayout, QFormLayout, QLineEdit, QMessageBox, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import pyqtSignal
from db import get_connection, hash_password

class MembersWindow(QWidget):
    data_changed = pyqtSignal()

    def __init__(self, role="MEMBER"):
        super().__init__()
        self.role = role
        self.setWindowTitle("Members Management")
        self.setGeometry(260, 160, 720, 520)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("<b>Members - View, Add, Edit, Delete</b>"))

        ctrl_h = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh"); self.refresh_btn.clicked.connect(self.load_members)
        self.edit_btn = QPushButton("Edit Selected"); self.edit_btn.clicked.connect(self.edit_selected)
        self.delete_btn = QPushButton("Delete Selected"); self.delete_btn.clicked.connect(self.delete_selected)
        ctrl_h.addWidget(self.refresh_btn); ctrl_h.addWidget(self.edit_btn); ctrl_h.addWidget(self.delete_btn)
        layout.addLayout(ctrl_h)

        self.table = QTableWidget(); layout.addWidget(self.table)

        form = QFormLayout()
        self.input_username = QLineEdit(); self.input_fullname = QLineEdit(); self.input_phone = QLineEdit(); self.input_password = QLineEdit()
        self.add_btn = QPushButton("Add Member (optionally create user)"); self.add_btn.clicked.connect(self.add_member)
        form.addRow("Username (optional):", self.input_username); form.addRow("Full Name:", self.input_fullname)
        form.addRow("Phone:", self.input_phone); form.addRow("Password (optional):", self.input_password); form.addRow(self.add_btn)
        layout.addLayout(form)

        self.setLayout(layout)
        self.apply_permissions()
        self.load_members()

    def apply_permissions(self):
        # Admin: cannot add (per spec) but can delete and change settings
        if self.role == "ADMIN":
            self.add_btn.setEnabled(False)
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(True)
        elif self.role == "LIBRARIAN":
            self.add_btn.setEnabled(True)
            self.edit_btn.setEnabled(True)
            self.delete_btn.setEnabled(False)
        else:
            self.add_btn.setEnabled(False)
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)

    def warn_conn(self):
        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "DB Error", "Cannot connect to database.")
        return conn

    def load_members(self):
        conn = self.warn_conn(); 
        if not conn: return
        cur = conn.cursor()
        cur.execute("""
            SELECT m.member_id, m.user_id, m.full_name, m.phone, m.status, u.username
            FROM members m
            LEFT JOIN users u ON m.user_id = u.user_id
            ORDER BY m.member_id
        """)
        rows = cur.fetchall()
        cur.close(); conn.close()
        self.table.setRowCount(len(rows))
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID","UserID","Full Name","Phone","Status","Username"])
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(val) if val is not None else ""))

    def add_member(self):
        if self.role != "LIBRARIAN":
            QMessageBox.warning(self, "Permission denied", "Only librarians can add members.")
            return
        username = self.input_username.text().strip()
        fullname = self.input_fullname.text().strip()
        phone = self.input_phone.text().strip()
        password = self.input_password.text().strip()
        if not fullname:
            QMessageBox.warning(self, "Input Error", "Full name required."); return
        conn = self.warn_conn(); 
        if not conn: return
        cur = conn.cursor()
        try:
            user_id = None
            if username:
                cur.execute("SELECT user_id FROM users WHERE username = %s", (username,))
                res = cur.fetchone()
                if res:
                    user_id = res[0]
                else:
                    cur.execute("SELECT role_id FROM roles WHERE role_name = 'MEMBER' LIMIT 1")
                    rr = cur.fetchone(); role_id = rr[0] if rr else 3
                    pwd_hash = hash_password(password) if password else hash_password("member123")
                    cur.execute("INSERT INTO users (username, password_hash, role_id) VALUES (%s,%s,%s) RETURNING user_id",
                                (username, pwd_hash, role_id))
                    user_id = cur.fetchone()[0]
            cur.execute("INSERT INTO members (user_id, full_name, phone) VALUES (%s,%s,%s)", (user_id, fullname, phone))
            conn.commit()
            cur.close(); conn.close()
            QMessageBox.information(self, "Success", "Member added.")
            self.data_changed.emit()
            self.load_members()
        except Exception as e:
            conn.rollback(); cur.close(); conn.close()
            QMessageBox.critical(self, "DB Error", f"Failed to add member: {e}")

    def selected_member(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select", "Select a member row first."); return None
        try:
            data = [self.table.item(row, c).text() if self.table.item(row, c) else None for c in range(self.table.columnCount())]
            return tuple(data)
        except Exception:
            QMessageBox.warning(self, "Error", "Could not read selected row."); return None

    def edit_selected(self):
        if self.role != "LIBRARIAN":
            QMessageBox.warning(self, "Permission denied", "Only librarians can edit members."); return
        member = self.selected_member()
        if not member: return
        dlg = QDialog(self); dlg.setWindowTitle("Edit Member"); form = QFormLayout(dlg)
        fullname = QLineEdit(member[2]); phone = QLineEdit(member[3] or ""); status = QLineEdit(member[4] or "ACTIVE")
        form.addRow("Full Name:", fullname); form.addRow("Phone:", phone); form.addRow("Status:", status)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel); buttons.accepted.connect(dlg.accept); buttons.rejected.connect(dlg.reject); form.addWidget(buttons)
        if dlg.exec_() == QDialog.Accepted:
            conn = self.warn_conn(); 
            if not conn: return
            cur = conn.cursor()
            try:
                cur.execute("UPDATE members SET full_name=%s, phone=%s, status=%s WHERE member_id=%s",
                            (fullname.text().strip(), phone.text().strip(), status.text().strip(), int(member[0])))
                conn.commit(); cur.close(); conn.close()
                QMessageBox.information(self, "Success", "Member updated.")
                self.data_changed.emit(); self.load_members()
            except Exception as e:
                conn.rollback(); cur.close(); conn.close()
                QMessageBox.critical(self, "DB Error", f"Failed to update member: {e}")

    def delete_selected(self):
        if self.role != "ADMIN":
            QMessageBox.warning(self, "Permission denied", "Only Admin can delete members."); return
        member = self.selected_member(); 
        if not member: return
        try:
            member_id = int(member[0])
        except Exception:
            QMessageBox.warning(self, "Error", "Invalid member selected."); return
        ok = QMessageBox.question(self, "Confirm Delete", f"Delete member ID {member_id}?")
        if ok != QMessageBox.Yes: return
        conn = self.warn_conn(); 
        if not conn: return
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM members WHERE member_id=%s", (member_id,))
            conn.commit(); cur.close(); conn.close()
            QMessageBox.information(self, "Deleted", "Member deleted.")
            self.data_changed.emit(); self.load_members()
        except Exception as e:
            conn.rollback(); cur.close(); conn.close()
            QMessageBox.critical(self, "DB Error", f"Failed to delete member: {e}")
