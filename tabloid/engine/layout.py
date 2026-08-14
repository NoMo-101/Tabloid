import networkx as nx

class LayoutEngine:
    """Calculates 2D canvas coordinates for database schema nodes.

    Combines NetworkX graph layout algorithms (Kamada-Kawai) with an iterative
    Axis-Aligned Bounding Box (AABB) de-overlap pass to prevent visual node clipping.
    """
    def __init__(self, tables, foreign_keys):
        """Initializes engine with table and foreign key metadata models.

        Args:
            tables (list[TableInfo]): List of tables to represent as graph nodes.
            foreign_keys (list[ForeignKeyInfo]): Foreign key relationships to represent as graph edges.
        """
        self.tables = tables
        self.foreign_keys = foreign_keys
    
    def build_graph(self):
        """Constructs an undirected NetworkX Graph from tables and foreign keys.

        Returns:
            nx.Graph: Graph object where nodes represent tables and edges represent foreign key relationships.
        """
        db_graph = nx.Graph()
        table_names = [table.table_name for table in self.tables]
        db_graph.add_nodes_from(table_names)
        db_graph.add_edges_from([(fk.from_table, fk.to_table) for fk in self.foreign_keys])
        return db_graph
    
    def compute_layout(self):
        """Generates initial 2D coordinate positions using the Kamada-Kawai force-directed algorithm.

        Returns:
            dict[str, tuple[float, float]]: Mapping of table names to raw abstract (x, y) coordinates.
        """
        graph = self.build_graph()
        position = nx.kamada_kawai_layout(graph)
        return position

    def space_nodes(self, positions, width, height):        #this method spaces out nodes so when the schema is render initially there is not overlapping 
        """Applies an iterative AABB collision-resolution algorithm to resolve bounding box overlaps.

        Args:
            positions: Initial node coordinates scaled to pixel space.
            width: Node width boundary (e.g., TableNode.WIDTH).
            height: Node height boundary (e.g., TableNode.COLLAPSED_HEIGHT).

        Returns:
            dict[str, tuple[float, float]]: Updated node coordinate mapping guaranteed free of overlap
                (or capped at MAX_PASSES).
        """
        MAX_PASSES = 100
        passes = 0


        while True:
            passes += 1
            items = list(positions.items())
            any_overlap = False


            # Pairwise AABB overlap evaluation across all nodes
            for i in range(len(items)):
                for j in range(i + 1, len(items)):
                    table_A_name = items[i][0]
                    table_B_name = items[j][0]
                    table_A_pos = items[i][1]
                    table_B_pos = items[j][1]

                    x1, y1 = table_A_pos
                    x2, y2 = table_B_pos
                    w1 = w2 = width
                    h1 = h2 = height

                    # Check for box intersection along both axes
                    horizontal_overlap = x1 < x2 + w2 and x2 < x1 + w1
                    vertical_overlap = y1 < y2 + h2 and y2 < y1 + h1

                    if horizontal_overlap and vertical_overlap:
                        any_overlap = True
                        overlap_x = abs((x1 + w1) - x2)
                        overlap_y = abs((y1 + h1) - y2)

                        # Separate along the axis of minimum penetration depth
                        if overlap_x < overlap_y:
                            if x1 < x2:
                                new_x1 = x1 - (overlap_x / 2)
                                new_x2 = x2 + (overlap_x / 2)
                            else:
                                new_x1 = x1 + (overlap_x / 2)
                                new_x2 = x2 - (overlap_x / 2)
                            positions[table_A_name] = (new_x1, y1)
                            positions[table_B_name] = (new_x2, y2)
                        elif overlap_y < overlap_x:
                            if y1 < y2:
                                new_y1 = y1 - (overlap_y / 2)
                                new_y2 = y2 + (overlap_y / 2)
                            else:
                                new_y1 = y1 + (overlap_y / 2)
                                new_y2 = y2 - (overlap_y / 2)
                            positions[table_A_name] = (x1, new_y1)
                            positions[table_B_name] = (x2, new_y2)

            # Exit loop if no collisions remain or iteration threshold is reached
            if not any_overlap or passes >= MAX_PASSES:
                break

        return positions
