import os

from PyQt6.QtWidgets import QMainWindow, QGraphicsScene, QDialog, QMessageBox
from tabloid.engine.controller import Controller
from tabloid.ui.canvas import Edge, TableNode, SchemaCanvas
from tabloid.ui.connection_dialog import ConnectionDialog
from tabloid.engine.layout import LayoutEngine
from PyQt6.QtGui import QAction, QBrush, QColor
from PyQt6.QtCore import QObject, pyqtSignal

class DiffSignalEmitter(QObject):
    """Signal bridge to safely hand off Git watcher events from background threads to the main Qt GUI thread."""

    diff_ready = pyqtSignal(dict)


class UIWindow(QMainWindow):
    """Main application window for Tabloid.

    Manages database connection workflows, schema canvas rendering, menu bar
    actions, and background file system/Git event listeners.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tabloid")
        self.resize(1200, 800)

        # Initialize interactive graphics canvas
        self.scene = QGraphicsScene()
        self.view = SchemaCanvas(self.scene, self.reset_colors)
        self.setCentralWidget(self.view)

        # Thread-safe signal bridge for background Git watcher notifications
        self.diff_emitter = DiffSignalEmitter()
        self.diff_emitter.diff_ready.connect(self.show_diff_popup)

        # Global action menu for re-fetching schema metadata
        refresh_action = QAction("Refresh Schema", self)
        refresh_action.triggered.connect(self.refresh_schema)
        self.menuBar().addAction(refresh_action) # not clean but it adds "Refresh Schema" button to top of Tabloid UI - for fetching

        # Prompt for credentials; schedule object destruction if connection is cancelled
        if self.load_schema():
            self.render_schema()
        else:
            self.deleteLater()

    def load_schema(self):
        """Displays connection modal, authenticates database, and initializes repository watching.

        Returns:
            bool: True if connection succeeded and schema was loaded; False if user cancelled.
        """
        self.controller = Controller() # added self to store for later use

        # Re-prompt on connection failure until successful or user cancels modal
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

            # Store schema metadata for layout calculations and canvas rendering
            self.tables = tables
            self.foreign_keys = foreign_keys
            self.columns = columns
            self.positions = positions
            self.graph = graph
            self.connection_id = connection_id

            # Initialize optional local repository watcher for schema migration tracking
            if credentials["repo_path"]:
                if os.path.isdir(credentials["repo_path"]):
                    try:
                        self.controller.start_git_watcher(credentials["repo_path"], self.diff_emitter.diff_ready.emit) # eventually make a new column on connections table or a new table in local_db.py for repo picker menu
                    except ValueError as error:
                        QMessageBox.warning(self, "Git Watcher Failed", str(error))
                else:
                    QMessageBox.warning(
                        self, "Invalid Repo Path",
                        f"'{credentials['repo_path']}' is not a valid directory. Skipping git watcher."
                    )

            break
           
        return True


    def render_schema(self):
        """Calculates visual layout positioning and populates scene with nodes and edges."""
        self.scene.clear() # Wipes old existing canvas items prior to redraw

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

        # Optimize column lookup mapping by table name
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

       # Step 4: Draw relationship edges connecting table node pairs
        for fk in self.foreign_keys:
            from_node = node_map[fk.from_table]
            to_node = node_map[fk.to_table]
            edge = Edge(from_node, to_node)
            self.scene.addItem(edge)                                #Qt-dependent


    def refresh_schema(self):
        """Fetches fresh schema metadata from active database connection and re-renders canvas."""
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
        """Resets background fill of all TableNodes to default white (clears neighbor selection)."""
        for item in self.scene.items():                             #Qt-dependent
            if isinstance(item, TableNode):
                item.setBrush(QBrush(QColor("white")))              #Qt-dependent


    def show_diff_popup(self, diff: dict):
        """Displays dialog notification when Git watcher detects schema SQL file modifications."""
        if "error" in diff:
            QMessageBox.warning(self, "Git Watcher Error", diff["error"])
            return
        QMessageBox.information(self, "Schema Changed", f"Detected schema changes:\n\n{diff}")

