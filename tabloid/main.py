import sys

from PyQt6.QtWidgets import QApplication
from tabloid.storage.local_db import init_db
from tabloid.ui.main_window import UIWindow


def main():
    """Application entry point for Tabloid.

    Initializes local sqlite storage, configures the primary Qt application context,
    instantiates the main UI window, and executes the event loop.
    """
    # Initialize SQLite database schema for local app settings and connection history
    init_db()

    # Initialize Qt Application context; receives CLI arguments
    app = QApplication(sys.argv)

    # Instantiate main window (triggers database connection dialog on startup)
    window = UIWindow()

    # Display main window if database connection succeeded during init
    window.show()

    # Enter Qt main event loop; exits process with return code on app closure
    sys.exit(app.exec())


if __name__ == "__main__":
    main()