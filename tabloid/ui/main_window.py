from PyQt6.QtWidgets import QMainWindow, QGraphicsScene, QDialog, QMessageBox
from tabloid.engine.controller import Controller
from tabloid.ui.canvas import Edge, TableNode, SchemaCanvas
from tabloid.ui.connection_dialog import ConnectionDialog
from tabloid.engine.layout import LayoutEngine
from PyQt6.QtGui import QAction, QBrush, QColor


class UIWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tabloid")
        self.resize(1200, 800)
        self.scene = QGraphicsScene()
        self.view = SchemaCanvas(self.scene, self.reset_colors)
        self.setCentralWidget(self.view)

        refresh_action = QAction("Refresh Schema", self)
        refresh_action.triggered.connect(self.refresh_schema)
        self.menuBar().addAction(refresh_action) # not clean but it adds "Refresh Schema" button to top of Tabloid UI - for fetching

        if self.load_schema():
            self.render_schema()
        else:
            self.deleteLater()


    def load_schema(self):
        self.controller = Controller() # added self to store for later use
        
        while True:
            dialog = ConnectionDialog()
            if dialog.exec() == QDialog.DialogCode.Accepted:
                credentials = dialog.get_credentials()
            else:
                return False

            try:
                tables, foreign_keys, columns, positions, graph, connection_id = self.controller.connect_and_load_schema(credentials) # added self to call fetch_schema_snapshot()
            except ConnectionError as error:
                QMessageBox.critical(self, "Connection Failed", f"Could not connect to the database.\n\n{error}")
                continue

            self.tables = tables
            self.foreign_keys = foreign_keys
            self.columns = columns
            self.positions = positions
            self.graph = graph
            self.connection_id = connection_id

            self.controller.start_git_watcher(credentials["repo_path"], self.show_diff_popup) # eventually make a new column on connections table or a new table in local_db.py for repo picker menu

            break
           
        return True


    def render_schema(self):
        self.scene.clear() # wipes old before redrawing

        all_nodes = []
        node_map = {}

        # Step 1: scale raw Kamada-Kawai positions into pixel space, once, up front
        scaled_positions = {}
        for table_name, pos in self.positions.items():
            x = float(pos[0]) * 260 + 500
            y = float(pos[1]) * 220 + 400
            scaled_positions[table_name] = (x, y)
        self.positions = scaled_positions

        # Step 2: now positions and TableNode.WIDTH/COLLAPSED_HEIGHT are in the same coordinate system
        layout = LayoutEngine(self.tables, self.foreign_keys)
        self.positions = layout.space_nodes(self.positions, TableNode.WIDTH, TableNode.COLLAPSED_HEIGHT)

        columns_by_table = {}
        for column in self.columns:
            columns_by_table.setdefault(column.table_name, []).append(column)

        # Step 3: loop no longer needs to scale — positions are already pixel-scale
        # tweaked for loop for positions
        for table_name, pos in self.positions.items():
            x, y = pos
            neighbors = list(self.graph.neighbors(table_name))
            table_columns = [c for c in self.columns if c.table_name == table_name]
            node = TableNode(table_name, table_columns, neighbors, all_nodes)
            node.setPos(x, y)
            self.scene.addItem(node)
            all_nodes.append(node)
            node_map[table_name] = node

        # this is for the edges instead of positions (tweak: from_node & to_node was moved into canvas into Edge class)
        for fk in self.foreign_keys:
            from_node = node_map[fk.from_table]
            to_node = node_map[fk.to_table]
            edge = Edge(from_node, to_node)
            self.scene.addItem(edge)                                #Qt-dependent


    def refresh_schema(self):
        try:
            tables, foreign_keys, columns, positions, graph = self.controller.fetch_schema_snapshot() # calls the fetch from controller
        except RuntimeError as error:
            QMessageBox.critical(self, "Refresh Failed", str(error))
            return
        except Exception as error:
            QMessageBox.critical(self, "Error", f"Could not refresh schema. \n\n{error}")
            return
       
        self.tables = tables
        self.foreign_keys = foreign_keys
        self.columns = columns
        self.positions = positions
        self.graph = graph     
        self.render_schema()

       
    def reset_colors(self):
        for item in self.scene.items():                             #Qt-dependent
            if isinstance(item, TableNode):
                item.setBrush(QBrush(QColor("white")))              #Qt-dependent


    def show_diff_popup(self, diff):
        message = f"Added: {diff['added_tables']}, Removed: {diff['removed_tables']}"
        QMessageBox.information(self, "Schema Diff", message)

