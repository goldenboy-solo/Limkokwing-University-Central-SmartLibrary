# club.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton,
    QHBoxLayout, QFormLayout, QLineEdit, QMessageBox, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import pyqtSignal
from db import get_connection

class ClubWindow(QWidget):
    data_changed = pyqtSignal()

    def __init__(self, role="MEMBER"):
        super().__init__()
        self.role = role
        self.setWindowTitle("Book Clubs")
        self.setGeometry(260, 160, 720, 480)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("<b>Book Clubs - View & Add/Edit/Delete</b>"))

        ctrl = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh"); self.refresh_btn.clicked.connect(self.load_clubs)
        self.edit_btn = QPushButton("Edit Selected"); self.edit_btn.clicked.connect(self.edit_selected)
        self.delete_btn = QPushButton("Delete Selected"); self.delete_btn.clicked.connect(self.delete_selected)
        ctrl.addWidget(self.refresh_btn); ctrl.addWidget(self.edit_btn); ctrl.addWidget(self.delete_btn)
        layout.addLayout(ctrl)

        self.table = QTableWidget(); layout.addWidget(self.table)

        form = QFormLayout()
        self.input_name = QLineEdit(); self.input_desc = QLineEdit()
        self.add_btn = QPushButton("Add Club"); self.add_btn.clicked.connect(self.add_club)
        form.addRow("Club Name:", self.input_name); form.addRow("Description:", self.input_desc); form.addRow(self.add_btn)
        layout.addLayout(form)

        self.setLayout(layout)
        self.apply_permissions()
        self.load_clubs()

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

    def load_clubs(self):
        conn = self.warn_conn(); 
        if not conn: return
        cur = conn.cursor()
        cur.execute("""
            SELECT bc.club_id, bc.club_name, bc.description, COUNT(bcm.member_id) AS members_count
            FROM book_clubs bc
            LEFT JOIN book_club_members bcm ON bc.club_id = bcm.club_id
            GROUP BY bc.club_id, bc.club_name, bc.description
            ORDER BY bc.club_id
        """)
        rows = cur.fetchall()
        cur.close(); conn.close()
        self.table.setRowCount(len(rows)); self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID","Name","Description","Members Count"])
        for i, r in enumerate(rows):
            for j, val in enumerate(r):
                self.table.setItem(i, j, QTableWidgetItem(str(val) if val is not None else ""))

    def add_club(self):
        if self.role != "LIBRARIAN":
            QMessageBox.warning(self, "Permission denied", "Only librarians can add clubs."); return
        name = self.input_name.text().strip(); desc = self.input_desc.text().strip()
        if not name: QMessageBox.warning(self, "Input Error", "Club name required."); return
        conn = self.warn_conn(); 
        if not conn: return
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO book_clubs (club_name, description) VALUES (%s,%s)", (name, desc))
            conn.commit(); cur.close(); conn.close(); QMessageBox.information(self, "Success", "Club added.")
            self.data_changed.emit(); self.load_clubs()
        except Exception as e:
            conn.rollback(); cur.close(); conn.close(); QMessageBox.critical(self, "DB Error", f"Failed to add club: {e}")

    def selected_club(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select", "Select a club row first."); return None
        try:
            data = [self.table.item(row, c).text() if self.table.item(row, c) else None for c in range(self.table.columnCount())]
            return tuple(data)
        except Exception:
            QMessageBox.warning(self, "Error", "Could not read selected row."); return None

    def edit_selected(self):
        if self.role != "LIBRARIAN":
            QMessageBox.warning(self, "Permission denied", "Only librarians can edit clubs."); return
        club = self.selected_club(); 
        if not club: return
        dlg = QDialog(self); dlg.setWindowTitle("Edit Club"); form = QFormLayout(dlg)
        name = QLineEdit(club[1]); desc = QLineEdit(club[2] or ""); form.addRow("Club Name:", name); form.addRow("Description:", desc)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel); buttons.accepted.connect(dlg.accept); buttons.rejected.connect(dlg.reject); form.addWidget(buttons)
        if dlg.exec_() == QDialog.Accepted:
            conn = self.warn_conn(); 
            if not conn: return
            cur = conn.cursor()
            try:
                cur.execute("UPDATE book_clubs SET club_name=%s, description=%s WHERE club_id=%s",
                            (name.text().strip(), desc.text().strip(), int(club[0])))
                conn.commit(); cur.close(); conn.close(); QMessageBox.information(self, "Success", "Club updated.")
                self.data_changed.emit(); self.load_clubs()
            except Exception as e:
                conn.rollback(); cur.close(); conn.close(); QMessageBox.critical(self, "DB Error", f"Failed to update club: {e}")

    def delete_selected(self):
        if self.role != "ADMIN":
            QMessageBox.warning(self, "Permission denied", "Only Admin can delete clubs."); return
        club = self.selected_club(); 
        if not club: return
        try:
            club_id = int(club[0])
        except Exception:
            QMessageBox.warning(self, "Error", "Invalid club selected."); return
        ok = QMessageBox.question(self, "Confirm Delete", f"Delete club '{club[1]}' (ID {club_id})?")
        if ok != QMessageBox.Yes: return
        conn = self.warn_conn(); 
        if not conn: return
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM book_clubs WHERE club_id = %s", (club_id,))
            conn.commit(); cur.close(); conn.close()
            QMessageBox.information(self, "Deleted", "Club deleted.")
            self.data_changed.emit(); self.load_clubs()
        except Exception as e:
            conn.rollback(); cur.close(); conn.close(); QMessageBox.critical(self, "DB Error", f"Failed to delete club: {e}")
