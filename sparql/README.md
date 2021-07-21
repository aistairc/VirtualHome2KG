# Example SPARQL queries

## Example 1
A SPARQL query to obtain :State instances of objects in the situation before executing the first action and after executing the final actions of each activity. Please replace %activity to URI.

```sql
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX : <http://example.org/virtualhome2kg/ontology/>
PREFIX ho: <http://www.owl-ontologies.com/VirtualHome.owl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
select distinct ?firstState ?firstStateType ?firstObject ?finalState ?finalStateType ?finalObject where {
    {
        select  (Max(?number) as ?max) where {
            <%activity> :action ?action .
            ?action :actionNumber ?number .
        }
    }
    <%activity> :action ?firstAction ;
              :action ?finalAction .
    ?firstAction :actionNumber "0"^^xsd:int ;
            :situationBeforeAction ?firstSituation ;
            :object ?firstObject .
    ?firstState :partOf ?firstSituation ;
                :isStateOf ?firstObject .
    optional {?firstState :state ?firstStateType .}
    ?finalAction :actionNumber ?max ;
            :situationAfterAction ?finalSituation ;
            :object ?finalObject .
    ?finalState :partOf ?finalSituation ;
                :isStateOf ?finalObject .
    optional {?finalState :state ?finalStateType .}
}
```

## Example 2
A SPARQL query to create a triple &lt;activity1, :nextActivity, activity2&gt;, and update object states.  
Warning: This query does INSERT and DELETE.

```sql
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX : <http://example.org/virtualhome2kg/ontology/>
PREFIX ho: <http://www.owl-ontologies.com/VirtualHome.owl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
DELETE {
    ?firstState ?p ?o .
} INSERT { 
    ?activity1 :nextActivity ?activity2 .
    ?finalState :partOf ?situation ; 
                :nextState ?nextState .
} WHERE {
    {
        SELECT ?activity1 (Max(?number) as ?max) WHERE {
            BIND(<%activity1> AS ?activity1)
            ?activity1 :action ?action .
            ?action :actionNumber ?number .
        } group by ?activity1
    }
    ?activity1 :action ?finalAction .
    ?finalAction :actionNumber ?finalNumber ;
            :situationAfterAction ?finalSituation .
    ?finalState :partOf ?finalSituation ;
                :isStateOf ?object .
    filter(?finalNumber = ?max)
    BIND(<%activity2> AS ?activity2)
    ?activity2 :action ?firstAction .
    ?firstAction :actionNumber "0"^^xsd:int ;
            :situationBeforeAction ?firstSituation .
    ?firstState :partOf ?firstSituation ;
                :isStateOf ?object ;
                :partOf ?situation ;
                ?p ?o.
    optional {?firstState :nextState ?nextState}
}

```

## Example 3

A SPARQL query to search for frequently grabbed objects.
```sql
PREFIX ho: <http://www.owl-ontologies.com/VirtualHome.owl#>
PREFIX ex: <http://example.org/virtualhome2kg/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX : <http://example.org/virtualhome2kg/ontology/>
PREFIX dcterms: <http://purl.org/dc/terms/>
select (concat(?label,?id) AS ?name) (count(?object) AS ?count) where { 
	?objectClass rdfs:subClassOf ex:Object .
    ?object a ?objectClass ;
            rdfs:label ?label ; 
            dcterms:identifier ?id .
    ?action ho:object ?object .
    ?action a ex:Grab .
} group by ?object ?label ?id order by desc(count(?object)) limit 20
``` 

## Example 4

A SPARQL query to search for the objects whose state changes frequently.
```sql
PREFIX : <http://example.org/virtualhome2kg/ontology/>
PREFIX ho: <http://www.owl-ontologies.com/VirtualHome.owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX dcterms: <http://purl.org/dc/terms/>
select distinct (concat(?label,?id) AS ?name) (count(?nextState) AS ?cnt) where {
    ?object a ?objectClass ;
            rdfs:label ?label ;
            dcterms:identifier ?id .
    ?objectClass rdfs:subClassOf+ :Object .
    ?objectState :isStateOf ?object.
    ?objectState :nextState ?nextState .
    #?objectState :affordance :GRABBABLE .
    filter (?objectClass != <http://example.org/virtualhome2kg/instance/character>)
} group by ?object ?label ?id order by desc(count(?nextState)) limit 20

```

## Example 5

A SPARQL query to search for the types of frequently performed activities after wash_teeth. First, you have to change to the repository, which includes the augmented KG.
```sql
PREFIX ho: <http://www.owl-ontologies.com/VirtualHome.owl#>
PREFIX : <http://example.org/virtualhome2kg/ontology/>
select distinct ?a1Class (count(?a1) AS ?count) where { 
	?a1 :nextActivity ?a2 .
    ?a2 a ho:wash_teeth .
    ?a1 a ?a1Class
} group by ?a1Class order by Desc(count(?a1))
```