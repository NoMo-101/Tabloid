from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsSceneMouseEvent, QGraphicsView
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush, QPen
from PyQt6.QtWidgets import (
    QGraphicsRectItem,
    QGraphicsTextItem,
    QGraphicsSceneMouseEvent,
    QGraphicsView,
)


class TableNode(QGraphicsRectItem):
    COLLAPSED_HEIGHT = 40
    ROW_HEIGHT = 20
    WIDTH = 220

    def __init__(self, table_name, columns, neighbors, all_nodes):
        super().__init__()

        self.table_name = table_name
        self.columns = columns
        self.neighbors = neighbors
        self.all_nodes = all_nodes

        self.expanded = False

        self.setBrush(QBrush(QColor("white")))
        self.setPen(QPen(Qt.GlobalColor.black))

        self.setRect(0, 0, self.WIDTH, self.COLLAPSED_HEIGHT)

        # Table title
        self.title = QGraphicsTextItem(table_name, self)
        self.title.setPos(8, 5)

        # Column information
        self.column_text = QGraphicsTextItem(self)
        self.column_text.setPos(8, 25)
        self.column_text.hide()

        self.update_column_text()  # Update the column text when the node is created

    def update_column_text(self):
        lines = []

        for column in self.columns:
            nullable = "YES" if column.is_nullable else "NO"

            lines.append(
                f"{column.column_name} | "
                f"{column.data_type} | "
                f"{nullable}"
            )

        self.column_text.setPlainText("\n".join(lines))

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        # Highlight blast radius
        for node in self.all_nodes:
            if node.table_name == self.table_name:
                node.setBrush(QBrush(QColor("skyblue")))
            elif node.table_name in self.neighbors:
                node.setBrush(QBrush(QColor("yellow")))
            else:
                node.setBrush(QBrush(QColor("white")))

        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event): # double click to expand node
        self.toggle_expand()
        super().mouseDoubleClickEvent(event)

    def toggle_expand(self): # toggles the actual expansion
        self.expanded = not self.expanded

        if self.expanded:
            self.column_text.show()
            height = (self.COLLAPSED_HEIGHT + len(self.columns) * self.ROW_HEIGHT)
            self.setRect(0, 0, self.WIDTH, height)
            self.setZValue(10)
        else:
            self.column_text.hide()
            self.setRect(0, 0, self.WIDTH, self.COLLAPSED_HEIGHT)
            self.setZValue(0)

class SchemaCanvas(QGraphicsView):
    def __init__(self, scene, reset_callback):
        super().__init__(scene)
        self.reset_callback = reset_callback

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if item is None:
            self.reset_callback()
        super().mousePressEvent(event)