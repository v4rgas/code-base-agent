import traceback
from io import StringIO

from blar_graph.db_managers import Neo4jManager
from blar_graph.graph_construction.core.graph_builder import GraphConstructor

repoId = "test"
entity_id = "test"
graph_manager = Neo4jManager(repoId, entity_id)

try:
    graph_constructor = GraphConstructor(
        root="../llama_index",
        graph_manager=graph_manager,
        entity_id=entity_id,
    )
    
    # Call the method you want to profile
    nodes, relationships = graph_constructor.build_graph()
except Exception as e:
    print(e)
    print(traceback.format_exc())
    graph_manager.close()
