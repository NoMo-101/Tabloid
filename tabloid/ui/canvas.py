from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsSceneMouseEvent, QGraphicsView
from PyQt6.QtGui import QBrush, QColor

class BlastRadius(QGraphicsRectItem):
    def __init__(self, table_name, neighbors, all_nodes):
        super().__init__()
        self.table_name = table_name
        self.neighbors = neighbors
        self.all_nodes = all_nodes
    
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent | None) -> None:
        for node in self.all_nodes:
            if node.table_name in self.neighbors:
                node.setBrush(QBrush(QColor("yellow")))
            elif node.table_name == self.table_name:
                node.setBrush(QBrush(QColor("blue")))
            else:
                node.setBrush(QBrush(QColor("white")))
        return super().mousePressEvent(event)

class SchemaCanvas(QGraphicsView):
    def __init__(self, scene, reset_callback):
        super().__init__(scene)
        self.reset_callback = reset_callback

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if item is None:
            self.reset_callback()
        return super().mousePressEvent(event)