from PyQt6.QtWidgets import QMainWindow, QGraphicsScene, QDialog, QMessageBox
from tabloid.db.postgres_connector import PostgresConnector
from tabloid.db.postgres_inspector import PostgresSchemaInspector
from tabloid.engine.layout import LayoutEngine
from tabloid.ui.canvas import BlastRadius, SchemaCanvas
from tabloid.ui.connection_dialog import ConnectionDialog
from PyQt6.QtGui import QBrush, QColor

class UIWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tabloid")
        self.resize(1200, 800)
        self.scene = QGraphicsScene()
        self.view = SchemaCanvas(self.scene, self.reset_colors)
        self.setCentralWidget(self.view)
        if self.load_schema():
            self.render_schema()

    def load_schema(self):
        while True:
            dialog = ConnectionDialog()
            if dialog.exec() == QDialog.DialogCode.Accepted:
                credentials = dialog.get_credentials()
            else:
                self.close()
                return False

            connector = PostgresConnector(
                credentials["host"],
                credentials["port"],
                credentials["user"],
                credentials["password"],
                credentials["dbname"]
            )

            if not connector.connect():
                QMessageBox.critical(self, "Connection Failed", "Could not connect to database. Check your credentials.")
                continue

            break

        inspector = PostgresSchemaInspector(connector)

        tables = inspector.fetch_tables()
        foreign_keys = inspector.fetch_foreign_keys()
        layout = LayoutEngine(tables, foreign_keys)
        positions = layout.compute_layout()

        self.tables = tables
        self.foreign_keys = foreign_keys
        self.positions = positions
        self.graph = layout.build_graph()

        return True

    def render_schema(self):
        all_nodes = []
        node_map = {}

        for table_name, pos in self.positions.items():
            x = float(pos[0]) * 200 + 500
            y = float(pos[1]) * 200 + 400
            neighbors = list(self.graph.neighbors(table_name))
            node = BlastRadius(table_name, neighbors, all_nodes)
            node.setRect(x, y, 160, 60)
            self.scene.addItem(node)
            all_nodes.append(node)
            node_map[table_name] = node
            text = self.scene.addText(table_name)
            if text:
                text.setPos(x, y)

        for fk in self.foreign_keys:
            from_pos = self.positions[fk.from_table]
            to_pos = self.positions[fk.to_table]
            x1 = float(from_pos[0]) * 200 + 500
            y1 = float(from_pos[1]) * 200 + 400
            x2 = float(to_pos[0]) * 200 + 500
            y2 = float(to_pos[1]) * 200 + 400
            self.scene.addLine(x1, y1, x2, y2)

    def reset_colors(self):
        for item in self.scene.items():
            if isinstance(item, BlastRadius):
                item.setBrush(QBrush(QColor("white")))