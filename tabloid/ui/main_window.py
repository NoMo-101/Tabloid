from PyQt6.QtWidgets import QMainWindow, QGraphicsScene, QDialog, QMessageBox
from tabloid.engine.controller import Controller
from tabloid.ui.canvas import TableNode, SchemaCanvas
from tabloid.ui.connection_dialog import ConnectionDialog
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

            break
            
        return True

    def render_schema(self):
        self.scene.clear() # wipes old before redrawing

        all_nodes = [] 
        node_map = {}

        columns_by_table = {}

        for column in self.columns:
            columns_by_table.setdefault(column.table_name, []).append(column)

        for table_name, pos in self.positions.items():              
            x = float(pos[0]) * 200 + 500                           
            y = float(pos[1]) * 200 + 400                           
            neighbors = list(self.graph.neighbors(table_name))      
            node = TableNode(table_name, columns_by_table.get(table_name, []), neighbors, all_nodes)    #Qt-dependent
            node.setPos(x, y)                                      #Qt-dependent
            self.scene.addItem(node)                                #Qt-dependent
            all_nodes.append(node)
            node_map[table_name] = node

        for fk in self.foreign_keys:                                
            from_pos = self.positions[fk.from_table]                
            to_pos = self.positions[fk.to_table]                    
            x1 = float(from_pos[0]) * 200 + 500                    
            y1 = float(from_pos[1]) * 200 + 400                     
            x2 = float(to_pos[0]) * 200 + 500                       
            y2 = float(to_pos[1]) * 200 + 400                       
            line = self.scene.addLine(x1, y1, x2, y2)
            line.setZValue(-1)                                          #Qt-dependent

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