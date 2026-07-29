from PyQt6.QtWidgets import QMainWindow, QGraphicsScene, QDialog, QMessageBox
from tabloid.engine.controller import Controller
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
        else:
            self.deleteLater()

    def load_schema(self):
        controller = Controller()

        while True:
            dialog = ConnectionDialog()
            if dialog.exec() == QDialog.DialogCode.Accepted:
                credentials = dialog.get_credentials()
            else:
                return False 

            try:
                tables, foreign_keys, positions, graph, connection_id = controller.connect_and_load_schema(credentials)
            except ConnectionError as error:
                QMessageBox.critical(self, "Connection Failed", f"Could not connect to the database.\n\n{error}")
                continue

            self.tables = tables
            self.foreign_keys = foreign_keys
            self.positions = positions
            self.graph = graph
            self.connection_id = connection_id

            break
            
        return True

    def render_schema(self):
        all_nodes = [] 
        node_map = {}

        for table_name, pos in self.positions.items():              
            x = float(pos[0]) * 200 + 500                           
            y = float(pos[1]) * 200 + 400                           
            neighbors = list(self.graph.neighbors(table_name))      
            node = BlastRadius(table_name, neighbors, all_nodes)    #Qt-dependent
            node.setRect(x, y, 160, 60)                             #Qt-dependent
            self.scene.addItem(node)                                #Qt-dependent
            all_nodes.append(node)
            node_map[table_name] = node
            text = self.scene.addText(table_name)                   #Qt-dependent
            if text:                                                #Qt-dependent
                text.setPos(x, y)                                   #Qt-dependent

        for fk in self.foreign_keys:                                
            from_pos = self.positions[fk.from_table]                
            to_pos = self.positions[fk.to_table]                    
            x1 = float(from_pos[0]) * 200 + 500                    
            y1 = float(from_pos[1]) * 200 + 400                     
            x2 = float(to_pos[0]) * 200 + 500                       
            y2 = float(to_pos[1]) * 200 + 400                       
            self.scene.addLine(x1, y1, x2, y2)                      #Qt-dependent

    def reset_colors(self):
        for item in self.scene.items():                             #Qt-dependent
            if isinstance(item, BlastRadius):
                item.setBrush(QBrush(QColor("white")))              #Qt-dependent