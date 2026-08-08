import networkx as nx

class LayoutEngine:
    def __init__(self, tables, foreign_keys):
        self.tables = tables
        self.foreign_keys = foreign_keys
    
    def build_graph(self):
        db_graph = nx.Graph()
        table_names = [table.table_name for table in self.tables]
        db_graph.add_nodes_from(table_names)
        db_graph.add_edges_from([(fk.from_table, fk.to_table) for fk in self.foreign_keys])
        return db_graph
    
    def compute_layout(self):
        graph = self.build_graph()
        position = nx.kamada_kawai_layout(graph)
        return position

    def space_nodes(self, positions, width, height):        #this method spaces out nodes so when the schema is render initially there is not overlapping 
        MAX_PASSES = 100
        passes = 0
        while True:
            passes += 1
            items = list(positions.items())
            any_overlap = False
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
                    horizontal_overlap = x1 < x2 + w2 and x2 < x1 + w1
                    vertical_overlap = y1 < y2 + h2 and y2 < y1 + h1
                    if horizontal_overlap and vertical_overlap:
                        any_overlap = True
                        overlap_x = abs((x1 + w1) - x2)
                        overlap_y = abs((y1 + h1) - y2)
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
            if not any_overlap or passes >= MAX_PASSES:
                break
        return positions
