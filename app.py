# app.py
import sys
from PyQt5.QtWidgets import QApplication
from login import LoginWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # load stylesheet
    try:
        with open("style.qss", "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except Exception as e:
        print("Could not load stylesheet:", e)

    login = LoginWindow()
    login.show()
    sys.exit(app.exec())
