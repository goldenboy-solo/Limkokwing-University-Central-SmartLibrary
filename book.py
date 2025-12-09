# book.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton,
    QHBoxLayout, QLineEdit, QFormLayout, QMessageBox, QSpinBox, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import pyqtSignal
from db import get_connection

class BooksWindow(QWidget):
    data_changed = pyqtSignal()

    def __init__(self, role="MEMBER"):
        super().__init__()
        self.setWindowTitle("Books Management")
        self.setGeometry(260, 160, 860, 540)
        self.role = role  # "ADMIN","LIBRARIAN","MEMBER"

        layout = QVBoxLayout()
        layout.addWidget(QLabel("<b>Books - View, Search & Add (permission controlled)</b>"))

        # Search + refresh
        s_h = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by title, author or ISBN...")
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.search_books)
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_books)
        s_h.addWidget(self.search_input)
        s_h.addWidget(self.search_btn)
        s_h.addWidget(self.refresh_btn)
        layout.addLayout(s_h)

        # Edit/Delete buttons (Admin can delete; Librarian can edit/add)
        actions_h = QHBoxLayout()
        self.edit_btn = QPushButton("Edit Selected")
        self.edit_btn.clicked.connect(self.edit_selected)
        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self.delete_selected)
        actions_h.addWidget(self.edit_btn)
        actions_h.addWidget(self.delete_btn)
        layout.addLayout(actions_h)

        # Table
        self.table = QTableWidget()
        layout.addWidget(self.table)

        # Add form: only allowed for Librarian
        self.form_allowed = (self.role == "LIBRARIAN")
        form = QFormLayout()
        self.input_title = QLineEdit()
        self.input_author_id = QLineEdit()
        self.input_isbn = QLineEdit()
        self.input_year = QLineEdit()
        self.input_total = QSpinBox(); self.input_total.setMinimum(1); self.input_total.setValue(1)
        self.add_btn = QPushButton("Add Book to Database")
        self.add_btn.clicked.connect(self.add_book)
        form.addRow("Title:", self.input_title)
        form.addRow("Author ID:", self.input_author_id)
        form.addRow("ISBN:", self.input_isbn)
        form.addRow("Year Published:", self.input_year)
        form.addRow("Total Copies:", self.input_total)
        form.addRow(self.add_btn)
        layout.addLayout(form)

        self.setLayout(layout)
        self.apply_permissions()
        self.load_books()

    def apply_permissions(self):
        # Admin: cannot add/edit/loan but can delete and settings (delete enabled, add/edit disabled)
        if self.role == "ADMIN":
            self.add_btn.setEnabled(False)
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(True)  # Admin can delete
        elif self.role == "LIBRARIAN":
            self.add_btn.setEnabled(True)
            self.edit_btn.setEnabled(True)
            self.delete_btn.setEnabled(False)
        else:  # Member
            self.add_btn.setEnabled(False)
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)

    def warn_conn(self):
        conn = get_connection()
        if not conn:
            QMessageBox.critical(self, "DB Error", "Cannot connect to database.")
        return conn

    def load_books(self):
        conn = self.warn_conn()
        if not conn: return
        cur = conn.cursor()
        cur.execute("""
            SELECT b.book_id, b.title, b.author_id, b.isbn, b.year_published, b.total_copies, b.available_copies,
                   a.first_name || ' ' || COALESCE(a.last_name,'') AS author_name
            FROM books b
            LEFT JOIN authors a ON b.author_id = a.author_id
            ORDER BY b.book_id
        """)
        rows = cur.fetchall()
        cur.close(); conn.close()

        self.table.setRowCount(len(rows))
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID","Title","AuthorID","ISBN","Year","Total","Available","AuthorName"])
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(val) if val is not None else ""))

    def search_books(self):
        q = self.search_input.text().strip()
        if not q:
            self.load_books(); return
        conn = self.warn_conn(); 
        if not conn: return
        cur = conn.cursor()
        cur.execute("""
            SELECT b.book_id, b.title, b.author_id, b.isbn, b.year_published, b.total_copies, b.available_copies,
                   a.first_name || ' ' || COALESCE(a.last_name,'') AS author_name
            FROM books b
            LEFT JOIN authors a ON b.author_id = a.author_id
            WHERE LOWER(b.title) LIKE LOWER(%s)
               OR LOWER(a.first_name || ' ' || COALESCE(a.last_name,'')) LIKE LOWER(%s)
               OR b.isbn LIKE %s
            ORDER BY b.book_id
        """, (f"%{q}%", f"%{q}%", f"%{q}%"))
        rows = cur.fetchall()
        cur.close(); conn.close()

        self.table.setRowCount(len(rows))
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID","Title","AuthorID","ISBN","Year","Total","Available","AuthorName"])
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(val) if val is not None else ""))

    def add_book(self):
        if self.role != "LIBRARIAN":
            QMessageBox.warning(self, "Permission denied", "Only librarians can add books.")
            return
        title = self.input_title.text().strip()
        author_id = self.input_author_id.text().strip()
        isbn = self.input_isbn.text().strip()
        year = self.input_year.text().strip()
        total = self.input_total.value()
        if not title or not author_id:
            QMessageBox.warning(self, "Input Error", "Title and Author ID are required.")
            return
        conn = self.warn_conn()
        if not conn: return
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO books (title, author_id, isbn, year_published, total_copies, available_copies)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (title, int(author_id), isbn or None, int(year) if year else None, total, total))
            conn.commit()
            cur.close(); conn.close()
            QMessageBox.information(self, "Success", "Book added.")
            self.data_changed.emit()
            self.load_books()
        except Exception as e:
            conn.rollback()
            cur.close(); conn.close()
            QMessageBox.critical(self, "DB Error", f"Failed to add book: {e}")

    def selected_book(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Selection", "Select a row first.")
            return None
        try:
            book_id = int(self.table.item(row, 0).text())
        except Exception:
            QMessageBox.warning(self, "Selection", "Invalid selection.")
            return None
        data = [self.table.item(row, c).text() if self.table.item(row, c) else None for c in range(self.table.columnCount())]
        return tuple(data)

    def edit_selected(self):
        if self.role != "LIBRARIAN":
            QMessageBox.warning(self, "Permission denied", "Only librarians can edit books.")
            return
        book = self.selected_book()
        if not book: return
        # open small edit dialog (reuse simpler inline editing)
        dlg = QDialog(self); dlg.setWindowTitle("Edit Book")
        form = QFormLayout(dlg)
        title_in = QLineEdit(book[1]); auth_in = QLineEdit(book[2]); isbn_in = QLineEdit(book[3] or "")
        year_in = QLineEdit(book[4] or ""); total_in = QSpinBox(); total_in.setMinimum(1); total_in.setValue(int(book[5]))
        form.addRow("Title:", title_in); form.addRow("Author ID:", auth_in); form.addRow("ISBN:", isbn_in)
        form.addRow("Year:", year_in); form.addRow("Total Copies:", total_in)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dlg.accept); buttons.rejected.connect(dlg.reject); form.addWidget(buttons)
        if dlg.exec_() == QDialog.Accepted:
            conn = self.warn_conn(); 
            if not conn: return
            cur = conn.cursor()
            try:
                # adjust available copies relative to change in total
                cur.execute("SELECT total_copies, available_copies FROM books WHERE book_id = %s", (int(book[0]),))
                cur_tot, cur_avail = cur.fetchone()
                new_total = int(total_in.value()); diff = new_total - cur_tot; new_avail = max(0, cur_avail + diff)
                cur.execute("""
                    UPDATE books SET title=%s, author_id=%s, isbn=%s, year_published=%s, total_copies=%s, available_copies=%s
                    WHERE book_id=%s
                """, (title_in.text().strip(), int(auth_in.text().strip()), isbn_in.text().strip() or None,
                      int(year_in.text().strip()) if year_in.text().strip() else None,
                      new_total, new_avail, int(book[0])))
                conn.commit()
                cur.close(); conn.close()
                QMessageBox.information(self, "Success", "Book updated.")
                self.data_changed.emit()
                self.load_books()
            except Exception as e:
                conn.rollback()
                cur.close(); conn.close()
                QMessageBox.critical(self, "DB Error", f"Failed to update book: {e}")

    def delete_selected(self):
        # Admin is allowed to delete; librarians not allowed here per your spec
        if self.role != "ADMIN":
            QMessageBox.warning(self, "Permission denied", "Only Admin can delete books.")
            return
        book = self.selected_book()
        if not book: return
        try:
            book_id = int(book[0]); title = book[1]
        except Exception:
            QMessageBox.warning(self, "Selection", "Invalid selection.")
            return
        ok = QMessageBox.question(self, "Confirm Delete", f"Delete book '{title}' (ID {book_id})? This may fail if FK constraints exist.")
        if ok != QMessageBox.Yes:
            return
        conn = self.warn_conn(); 
        if not conn: return
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM books WHERE book_id = %s", (book_id,))
            conn.commit()
            cur.close(); conn.close()
            QMessageBox.information(self, "Deleted", "Book deleted.")
            self.data_changed.emit()
            self.load_books()
        except Exception as e:
            conn.rollback()
            cur.close(); conn.close()
            QMessageBox.critical(self, "DB Error", f"Failed to delete book: {e}")