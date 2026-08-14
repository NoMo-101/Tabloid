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
    QListWidgetItem,
    QGraphicsLineItem
)




class TableNode(QGraphicsRectItem):
    """A visual canvas node representing a database table.

    Renders as a draggable rectangle with an expandable list of column definitions.
    Highlights connected neighbor nodes when selected.
    """
    COLLAPSED_HEIGHT = 40
    ROW_HEIGHT = 20
    WIDTH = 220


    MAX_VISIBLE_ROWS = 7 # Cap before enabling internal scrolling in column list
    MAX_EXPANDED_HEIGHT = COLLAPSED_HEIGHT + (MAX_VISIBLE_ROWS * ROW_HEIGHT)


    def __init__(self, table_name, columns, neighbors, all_nodes):
        super().__init__()


        self.edges = [] # Line relationships connected to this node


        self.table_name = table_name
        self.columns = columns
        self.neighbors = neighbors
        self.all_nodes = all_nodes
        self.expanded = False

        # Visual styling
        self.setBrush(QBrush(QColor("white")))
        self.setPen(QPen(Qt.GlobalColor.black))
        self.setRect(0, 0, self.WIDTH, self.COLLAPSED_HEIGHT)

        # Enable scene interaction capabilities
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable) # makes dragable/moveable
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable) # makes selectable
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)


        # Table header title
        self.title = QGraphicsTextItem(table_name, self)
        self.title.setPos(8, 5)


        # Scrollable column list widget embedded into graphics scene
        self.column_list = QListWidget()
        self.column_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.column_list.setStyleSheet("font-size: 11px;")
        for column in self.columns:
            nullable = "YES" if column.is_nullable else "NO"
            text = f"{column.column_name} | {column.data_type} | {nullable}"
            self.column_list.addItem(QListWidgetItem(text))

        # Proxy widget to host QListWidget inside QGraphicsScene
        self.column_proxy = QGraphicsProxyWidget(self)
        self.column_proxy.setWidget(self.column_list)
        self.column_proxy.setPos(4, self.COLLAPSED_HEIGHT)
        self.column_proxy.hide()


        # Fallback static text representation
        self.column_text = QGraphicsTextItem(self)
        self.column_text.setPos(8, 25)
        self.column_text.hide()


        self.update_column_text()  # Update the column text when the node is created


    def itemChange(self, change, value):
        """Intercepts scene geometry changes to update positions of connected edges while dragging."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged: #tweak: chaged ItemPositionChanged -> ItemPositionHasChanged
            for edge in self.edges:
                edge.update_position() # notifies whenever it an edge is moved
        return super().itemChange(change, value)


    def update_column_text(self):
        """Formats column metadata into plain text for the static text fallback component."""
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
        """Highlights the selected node (skyblue) and its directly connected foreign key neighbors (yellow)."""
        for node in self.all_nodes:
            if node.table_name == self.table_name:
                node.setBrush(QBrush(QColor("skyblue")))
            elif node.table_name in self.neighbors:
                node.setBrush(QBrush(QColor("yellow")))
            else:
                node.setBrush(QBrush(QColor("white")))

        super().mousePressEvent(event)


    def mouseDoubleClickEvent(self, event): # double click to expand node
        """Toggles the node expansion state on double-click."""
        self.toggle_expand()
        super().mouseDoubleClickEvent(event)


    def toggle_expand(self):
        """Expands or collapses the column list view and adjusts bounding geometry and edge connections."""
        self.expanded = not self.expanded

        if self.expanded:
            content_height = len(self.columns) * self.ROW_HEIGHT
            visible_height = min(content_height, self.MAX_VISIBLE_ROWS * self.ROW_HEIGHT)
            total_height = self.COLLAPSED_HEIGHT + visible_height


            self.column_list.setFixedSize(self.WIDTH - 8, visible_height)
            self.setRect(0, 0, self.WIDTH, total_height)
            self.column_proxy.show()
            self.setZValue(10) # Bring expanded node to front layer
        else:
            self.column_proxy.hide()
            self.setRect(0, 0, self.WIDTH, self.COLLAPSED_HEIGHT)
            self.setZValue(0) # Reset layer depth

        # Re-calculate connected edge positions to account for height changes
        for edge in self.edges:
            edge.update_position() 


class SchemaCanvas(QGraphicsView):
    """Custom interactive viewport for displaying schema graph nodes and edges.

    Triggers a reset callback when the user clicks empty canvas space.
    """
    def __init__(self, scene, reset_callback):
        super().__init__(scene)
        self.reset_callback = reset_callback

    def mousePressEvent(self, event):
        """Clears active selection highlighting if user clicks on empty canvas space."""
        item = self.itemAt(event.pos())
        if item is None:
            self.reset_callback()
        super().mousePressEvent(event)


class Edge(QGraphicsLineItem): # edge class that draws line from one node to another
    """Visual connector line representing a foreign key relationship between two TableNodes."""
    def __init__(self, from_node, to_node):
        super().__init__()
        self.from_node = from_node
        self.to_node = to_node
        # Register edge with both connected nodes for position tracking
        from_node.edges.append(self)        
        to_node.edges.append(self) 
               
        self.setPen(QPen(Qt.GlobalColor.black))
        self.setZValue(-1) # Render lines behind nodes
        self.update_position()


    def update_position(self):
        """Recalculates end points based on the current bounding box centers of connected nodes."""
        from_center = self.from_node.sceneBoundingRect().center()
        to_center = self.to_node.sceneBoundingRect().center()
        self.setLine(from_center.x(), from_center.y(), to_center.x(), to_center.y())

