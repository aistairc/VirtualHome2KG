#!/usr/bin/python
from owlready2 import *
my_world = World()
onto = my_world.get_ontology("sigswo56.rdf").load()
sync_reasoner_pellet([onto])
results = list(my_world.sparql("""
    PREFIX hra: <http://example.org/virtualhome2kg/ontology/homeriskactivitiy/>
    SELECT DISTINCT * WHERE {
        ?s rdf:type hra:RiskActivity .
    } limit 10"""))
print(results)
