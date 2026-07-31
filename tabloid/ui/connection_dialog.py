from PyQt6.QtWidgets import QDialog, QLineEdit, QFormLayout, QPushButton, QVBoxLayout

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
        self.connect_button.clicked.connect(self.accept)

        layout = QVBoxLayout()
        layout.addLayout(form)
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