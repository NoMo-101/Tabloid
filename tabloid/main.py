import sys
from PyQt6.QtWidgets import QApplication
from tabloid.ui.main_window import UIWindow
from tabloid.storage.local_db import init_db

init_db()
app = QApplication(sys.argv)
window = UIWindow()
window.show()
sys.exit(app.exec())