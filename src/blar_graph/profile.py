import traceback
import cProfile
import pstats
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
    
    # Create a Profile object
    pr = cProfile.Profile()

    # Enable profiling
    pr.enable()

    # Call the method you want to profile
    nodes, relationships = graph_constructor.build_graph()


    # Disable profiling
    pr.disable()

    # Create a string stream to capture the stats
    s = StringIO()
    sortby = pstats.SortKey.CUMULATIVE  # You can also use pstats.SortKey.TIME
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()

    # Print the profiling results
    print(s.getvalue())

except Exception as e:
    print(e)
    print(traceback.format_exc())
    graph_manager.close()
