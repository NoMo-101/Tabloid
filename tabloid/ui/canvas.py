from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsSceneMouseEvent, QGraphicsView
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush, QPen
from PyQt6.QtWidgets import (
    QGraphicsRectItem,
    QGraphicsTextItem,
    QGraphicsSceneMouseEvent,
    QGraphicsView,
    QGraphicsProxyWidget,
    QGraphicsItem,
    QListWidget,
    QListWidgetItem
)


class TableNode(QGraphicsRectItem):
    COLLAPSED_HEIGHT = 40
    ROW_HEIGHT = 20
    WIDTH = 220

    MAX_VISIBLE_ROWS = 7 # the cap before it starts scrolling
    MAX_EXPANDED_HEIGHT = COLLAPSED_HEIGHT + (MAX_VISIBLE_ROWS * ROW_HEIGHT)

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

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable) # makes dragable/moveable
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable) # makes selectable
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

        # Table title
        self.title = QGraphicsTextItem(table_name, self)
        self.title.setPos(8, 5)

        # column list, also make it scrollable...when needed obviously
        self.column_list = QListWidget()
        self.column_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.column_list.setStyleSheet("font-size: 11px;")
        for column in self.columns:
            nullable = "YES" if column.is_nullable else "NO"
            text = f"{column.column_name} | {column.data_type} | {nullable}"
            self.column_list.addItem(QListWidgetItem(text))

        self.column_proxy = QGraphicsProxyWidget(self)
        self.column_proxy.setWidget(self.column_list)
        self.column_proxy.setPos(4, self.COLLAPSED_HEIGHT)
        self.column_proxy.hide()

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

    def toggle_expand(self):
        self.expanded = not self.expanded

        if self.expanded:
            content_height = len(self.columns) * self.ROW_HEIGHT
            visible_height = min(content_height, self.MAX_VISIBLE_ROWS * self.ROW_HEIGHT)
            total_height = self.COLLAPSED_HEIGHT + visible_height

            self.column_list.setFixedSize(self.WIDTH - 8, visible_height)
            self.setRect(0, 0, self.WIDTH, total_height)
            self.column_proxy.show()
            self.setZValue(10)
        else:
            self.column_proxy.hide()
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