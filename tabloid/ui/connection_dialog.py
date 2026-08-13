from PyQt6.QtWidgets import QDialog, QLineEdit, QFormLayout, QPushButton, QVBoxLayout, QFileDialog, QMessageBox, QComboBox
from tabloid.git.validator import load_repo
from tabloid.storage.local_db import get_connections_for_repo, load_connection
from git.exc import InvalidGitRepositoryError

class ConnectionDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Connect to Database")
        self.resize(300, 200)
        self.saved_connection_menu = QComboBox()
        self.repo_path_input = QLineEdit()
        self.name_input = QLineEdit()
        self.host_input = QLineEdit("localhost")
        self.port_input = QLineEdit("5432")
        self.user_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.dbname_input = QLineEdit()
        self.saved_connection_menu.currentTextChanged.connect(self.on_connection_selected)
        

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
        layout.addWidget(self.saved_connection_menu)
        layout.addLayout(form)
        layout.addWidget(self.browse_button)
        layout.addWidget(self.connect_button)
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
                self.populate_saved_connections(path)
            except InvalidGitRepositoryError as error:
                QMessageBox.critical(self, "Connection Failed", f"Could not connect to the database.\n\n{error}")

    def populate_saved_connections(self, repo_path):
        self.saved_connection_menu.clear()
        connections = get_connections_for_repo(repo_path)
        for connection in connections:
            display_text = f"{connection['name']} ({connection['host']}:{connection['port']})"
            self.saved_connection_menu.addItem(display_text, connection["id"])
        

    def on_connection_selected(self):
        connection_id = self.saved_connection_menu.currentData()
        load = load_connection(connection_id)
        self.name_input.setText(load["connection"]["name"])
        self.host_input.setText(load["connection"]["host"])
        self.port_input.setText(str(load["connection"]["port"]))
        self.user_input.setText(load["connection"]["user"])
        self.dbname_input.setText(load["connection"]["dbname"])
        self.password_input.setText(load["password"])
