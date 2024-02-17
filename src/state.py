import rdflib

NAMESPACES = [
    ("bf", "http://id.loc.gov/ontologies/bibframe/"),
    ("sinopia", "http://sinopia.io/vocabulary/"),
]

SINOPIA_GRAPH = rdflib.Graph()

RESULTS_DF = None

for ns in NAMESPACES:
    SINOPIA_GRAPH.namespace_manager.bind(ns[0], ns[1])
