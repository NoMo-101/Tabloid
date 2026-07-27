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