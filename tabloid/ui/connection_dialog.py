from PyQt6.QtWidgets import QDialog, QLineEdit, QFormLayout, QPushButton, QVBoxLayout, QFileDialog, QMessageBox
from tabloid.git.validator import load_repo
from git.exc import InvalidGitRepositoryError

class ConnectionDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Connect to Database")
        self.resize(300, 200)
        self.repo_path_input = QLineEdit()
        self.name_input = QLineEdit()
        self.host_input = QLineEdit("localhost")
        self.port_input = QLineEdit("5432")
        self.user_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.dbname_input = QLineEdit()

        form = QFormLayout()
        form.addRow("Repo Path: ", self.repo_path_input)
        form.addRow("Name: ", self.name_input)
        form.addRow("Host: ", self.host_input)
        form.addRow("Port: ", self.port_input)
        form.addRow("User: ", self.user_input)
        form.addRow("Password: ", self.password_input)
        form.addRow("Database: ", self.dbname_input)

        self.connect_button = QPushButton("Connect")
        self.browse_button = QPushButton("Browse")
        self.connect_button.clicked.connect(self.accept)
        self.browse_button.clicked.connect(self.browse_for_repo)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self.connect_button)
        layout.addWidget(self.browse_button)
        self.setLayout(layout)

    def get_credentials(self):
        return {
            "repo_path": self.repo_path_input.text(),
            "name": self.name_input.text(),
            "host": self.host_input.text(),
            "port": int(self.port_input.text()) if self.port_input.text().strip() else 5432,
            "user": self.user_input.text(),
            "password": self.password_input.text(),
            "dbname": self.dbname_input.text()
        }

    def browse_for_repo(self):
        path = QFileDialog.getExistingDirectory(self, "Select Repository Folder")
        if path != "":
            try:
                load_repo(path)
                self.repo_path_input.setText(path)
            except InvalidGitRepositoryError as error:
                QMessageBox.critical(self, "Connection Failed", f"Could not connect to the database.\n\n{error}")
