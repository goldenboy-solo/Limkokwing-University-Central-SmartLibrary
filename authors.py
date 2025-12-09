# authors.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton,
    QHBoxLayout, QFormLayout, QLineEdit, QMessageBox, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import pyqtSignal
from db import get_connection

class AuthorsWindow(QWidget):
    data_changed = pyqtSignal()

    def __init__(self, role="MEMBER"):
        super().__init__()
        self.role = role
        self.setWindowTitle("Authors Management")
        self.setGeometry(280, 160, 700, 480)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("<b>Authors - View, Add, Edit, Delete</b>"))

        ctrl = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh"); self.refresh_btn.clicked.connect(self.load_authors)
        self.edit_btn = QPushButton("Edit Selected"); self.edit_btn.clicked.connect(self.edit_selected)
        self.delete_btn = QPushButton("Delete Selected"); self.delete_btn.clicked.connect(self.delete_selected)
        ctrl.addWidget(self.refresh_btn); ctrl.addWidget(self.edit_btn); ctrl.addWidget(self.delete_btn)
        layout.addLayout(ctrl)

        self.table = QTableWidget(); layout.addWidget(self.table)

        form = QFormLayout()
        self.input_first = QLineEdit(); self.input_last = QLineEdit(); self.input_bio = QLineEdit()
        self.add_btn = QPushButton("Add Author"); self.add_btn.clicked.connect(self.add_author)
        form.addRow("First Name:", self.input_first); form.addRow("Last Name:", self.input_last); form.addRow("Bio:", self.input_bio); form.addRow(self.add_btn)
        layout.addLayout(form)

        self.setLayout(layout)
        self.apply_permissions()
        self.load_authors()

    def apply_permissions(self):
        if self.role == "ADMIN":
            self.add_btn.setEnabled(False); self.edit_btn.setEnabled(False); self.delete_btn.setEnabled(True)
        elif self.role == "LIBRARIAN":
            self.add_btn.setEnabled(True); self.edit_btn.setEnabled(True); self.delete_btn.setEnabled(False)
        else:
            self.add_btn.setEnabled(False); self.edit_btn.setEnabled(False); self.delete_btn.setEnabled(False)

    def warn_conn(self):
        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "DB Error", "Cannot connect to database.")
        return conn

    def load_authors(self):
        conn = self.warn_conn(); 
        if not conn: return
        cur = conn.cursor()
        cur.execute("SELECT author_id, first_name, last_name, bio FROM authors ORDER BY author_id")
        rows = cur.fetchall()
        cur.close(); conn.close()
        self.table.setRowCount(len(rows)); self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID","First Name","Last Name","Bio"])
        for i, r in enumerate(rows):
            for j, val in enumerate(r):
                self.table.setItem(i, j, QTableWidgetItem(str(val) if val is not None else ""))

    def add_author(self):
        if self.role != "LIBRARIAN":
            QMessageBox.warning(self, "Permission denied", "Only librarians can add authors."); return
        first = self.input_first.text().strip(); last = self.input_last.text().strip(); bio = self.input_bio.text().strip()
        if not first:
            QMessageBox.warning(self, "Input Error", "First name required."); return
        conn = self.warn_conn(); 
        if not conn: return
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO authors (first_name, last_name, bio) VALUES (%s,%s,%s)", (first, last or None, bio or None))
            conn.commit(); cur.close(); conn.close()
            QMessageBox.information(self, "Success", "Author added.")
            self.data_changed.emit(); self.load_authors()
        except Exception as e:
            conn.rollback(); cur.close(); conn.close(); QMessageBox.critical(self, "DB Error", f"Failed to add author: {e}")

    def selected_author(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select", "Select an author row first."); return None
        try:
            data = [self.table.item(row, c).text() if self.table.item(row, c) else None for c in range(self.table.columnCount())]
            return tuple(data)
        except Exception:
            QMessageBox.warning(self, "Error", "Could not read selected row."); return None

    def edit_selected(self):
        if self.role != "LIBRARIAN":
            QMessageBox.warning(self, "Permission denied", "Only librarians can edit authors."); return
        author = self.selected_author(); 
        if not author: return
        dlg = QDialog(self); dlg.setWindowTitle("Edit Author"); form = QFormLayout(dlg)
        first = QLineEdit(author[1]); last = QLineEdit(author[2] or ""); bio = QLineEdit(author[3] or "")
        form.addRow("First Name:", first); form.addRow("Last Name:", last); form.addRow("Bio:", bio)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel); buttons.accepted.connect(dlg.accept); buttons.rejected.connect(dlg.reject); form.addWidget(buttons)
        if dlg.exec_() == QDialog.Accepted:
            conn = self.warn_conn(); 
            if not conn: return
            cur = conn.cursor()
            try:
                cur.execute("UPDATE authors SET first_name=%s, last_name=%s, bio=%s WHERE author_id=%s",
                            (first.text().strip(), last.text().strip() or None, bio.text().strip() or None, int(author[0])))
                conn.commit(); cur.close(); conn.close()
                QMessageBox.information(self, "Success", "Author updated."); self.data_changed.emit(); self.load_authors()
            except Exception as e:
                conn.rollback(); cur.close(); conn.close(); QMessageBox.critical(self, "DB Error", f"Failed to update author: {e}")

    def delete_selected(self):
        if self.role != "ADMIN":
            QMessageBox.warning(self, "Permission denied", "Only Admin can delete authors."); return
        author = self.selected_author(); 
        if not author: return
        try:
            author_id = int(author[0])
        except Exception:
            QMessageBox.warning(self, "Error", "Invalid author selected."); return
        ok = QMessageBox.question(self, "Confirm Delete", f"Delete author '{author[1]} {author[2] or ''}' (ID {author_id})? This may affect books.")
        if ok != QMessageBox.Yes: return
        conn = self.warn_conn(); 
        if not conn: return
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM authors WHERE author_id=%s", (author_id,))
            conn.commit(); cur.close(); conn.close()
            QMessageBox.information(self, "Deleted", "Author deleted.")
            self.data_changed.emit(); self.load_authors()
        except Exception as e:
            conn.rollback(); cur.close(); conn.close()
            QMessageBox.critical(self, "DB Error", f"Failed to delete author: {e}")
