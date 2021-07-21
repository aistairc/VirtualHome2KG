#!/usr/bin/env python3
import IPython.display
import sys
from rdflib import *
from rdflib.collection import Collection
import glob
import os
import re
import random
import csv
import itertools
from SPARQLWrapper import SPARQLWrapper, JSON, BASIC

def getStates():
    result = None
    queryString = """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX : <http://example.org/virtualhome2kg/ontology/>
    PREFIX ho: <http://www.owl-ontologies.com/VirtualHome.owl#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    select distinct ?firstState ?firstStateType ?firstObject ?finalState ?finalStateType ?finalObject ?activity where {
        {
            select ?activity (Max(?number) as ?max) where {
                ?activity a [rdfs:subClassOf+ ho:Activity] .
                ?activity :action ?action .
                ?action :actionNumber ?number .
            } group by ?activity
        }
        ?activity :action ?firstAction ;
                  :action ?finalAction .
        ?firstAction :actionNumber "0"^^xsd:int ;
                :situationBeforeAction ?firstSituation .
        ?firstState :partOf ?firstSituation ;
                    :isStateOf ?firstObject ;
                            :nextState ?nextState .
        optional {?firstState :state ?firstStateType .}
        ?finalAction :actionNumber ?finalNumber ;
                :situationAfterAction ?finalSituation .
        ?finalState :partOf ?finalSituation ;
                    :isStateOf ?finalObject .
        ?prevState :nextState ?finalState .
        optional {?finalState :state ?finalStateType .}
        filter(?finalNumber = ?max)
    }
    """
    sparql = SPARQLWrapper("http://localhost:7200/repositories/VirtualHome2Kg")

    sparql.setQuery(queryString)
    sparql.setReturnFormat(JSON)

    try :
        json = sparql.query().convert()
        bindings = json['results']['bindings']
        result = bindings
    except  Exception as e:
        print(e)
    
    return result

def readRoutine(path):
    with open(path) as f:
        reader = csv.reader(f)
        l = [row for row in reader][0]
        return l

def getActivity(activity_name):
    result = None
    queryString = """
        PREFIX : <http://example.org/virtualhome2kg/ontology/>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX ho: <http://www.owl-ontologies.com/VirtualHome.owl#>
        select distinct *
        where { 
            ?s a ho:%s
        }
    """
    sparql = SPARQLWrapper("http://localhost:7200/repositories/VirtualHome2Kg")

    sparql.setQuery(queryString % activity_name)
    sparql.setReturnFormat(JSON)

    try :
        json = sparql.query().convert()
        bindings = json['results']['bindings']
        result = bindings[0]['s']['value']
    except  Exception as e:
        print(e)
        result = e
    return result

def checkConsistency(activity1_value, activity2_value):
    finalStateList1 = activity1_value["finalState"]
    firstStateList2 = activity2_value["firstState"]
    executable = True
    for finalState in finalStateList1:
        finalStateObject = stateMap[finalState]["object"]
        finalStateTypes = stateMap[finalState]["state"]
        for firstState in firstStateList2:
            firstStateObject = stateMap[firstState]["object"]
            firstStateTypes = stateMap[firstState]["state"]
            if finalStateObject == firstStateObject:
                for finalStateType in finalStateTypes:
                    if finalStateType in inverse_states:
                        if inverse_states[finalStateType] in firstStateTypes:
                            print([finalStateType, firstStateTypes])
                            #さらに、そのobjectがactivtyの対象になっているかチェックし、対象となっていなければ上書きする
                            executable = checkTargetObject(firstState)
                            assert executable
                    else:
                        #print([finalState, firstState])
                        continue
    return executable

def checkTargetObject(state):
    queryString = """
        PREFIX : <http://example.org/virtualhome2kg/ontology/>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX ho: <http://www.owl-ontologies.com/VirtualHome.owl#>
        ASK { 
            <%s> :partOf ?situation ;
                      :isStateOf ?object .
            ?action (:situationBeforeAction|:situationAfterAction) ?situation .
            ?activity :action ?action ;
                      :action ?allActions .
            ?allActions ho:object ?object .
        }
    """
    sparql = SPARQLWrapper("http://localhost:7200/repositories/VirtualHome2Kg")

    sparql.setQuery(queryString % state)
    sparql.setReturnFormat(JSON)

    try :
        json = sparql.query().convert()
        if json['boolean'] is True:
            result = False
        else:
            result = True
    except  Exception as e:
        print(e)
        result = e
    return result

def update(activity1, activity2):
    result = None
    queryString = """
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
    """
    sparql = SPARQLWrapper("http://localhost:7200/repositories/VirtualHome2Kg_test/statements")
    sparql.setHTTPAuth(BASIC)
    sparql.setCredentials('admin', '')
    sparql.method = "POST"
    sparql.queryType = "INSERT"
    queryString = queryString.replace("%activity1", activity1)
    queryString = queryString.replace("%activity2", activity2)
    sparql.setQuery(queryString)
    sparql.setReturnFormat(JSON)
    
    try :
        json = sparql.query().convert()
        bindings = json
        result = bindings
    except  Exception as e:
        print(e)
    return result

if __name__ == "__main__":
    inverse_states = {
        "http://example.org/virtualhome2kg/ontology/CLOSED": "http://example.org/virtualhome2kg/ontology/OPEN",
        "http://example.org/virtualhome2kg/ontology/OFF": "http://example.org/virtualhome2kg/ontology/ON",
        "http://example.org/virtualhome2kg/ontology/DIRTY": "http://example.org/virtualhome2kg/ontology/CLEAN",
        "http://example.org/virtualhome2kg/ontology/PLUGGED_IN": "http://example.org/virtualhome2kg/ontology/PLUGGED_OUT",
        "http://example.org/virtualhome2kg/ontology/OPEN": "http://example.org/virtualhome2kg/ontology/CLOSED",
        "http://example.org/virtualhome2kg/ontology/ON": "http://example.org/virtualhome2kg/ontology/OFF",
        "http://example.org/virtualhome2kg/ontology/CLEAN": "http://example.org/virtualhome2kg/ontology/DIRTY",
        "http://example.org/virtualhome2kg/ontology/PLUGGED_OUT": "http://example.org/virtualhome2kg/ontology/PLUGGED_IN"
    }
    
    # get object states
    bindings = getStates()

    # preprocess
    activityMap = {}
    stateMap = {}
    for elem in bindings:
        activity = elem['activity']['value']
        firstState = elem['firstState']['value']
        finalState = elem['finalState']['value']
        #firstStateに関してstateMapの作成
        if 'firstStateType' in elem:
            if firstState not in stateMap:
                stateMap[firstState] = {
                    "state": [elem['firstStateType']['value']],
                    "object": elem['firstObject']['value']
                }
            else:
                if elem['firstStateType']['value'] not in stateMap[firstState]['state']:
                    stateMap[firstState]['state'].append(elem['firstStateType']['value'])
        else:
            if firstState not in stateMap:
                stateMap[firstState] = {
                    "state": [],
                    "object": elem['firstObject']['value']
                }
            else:
                pass
        
        #finalStateに関してstateMapの作成
        if  'finalStateType' in elem:
            if finalState not in stateMap:
                stateMap[finalState] = {
                    "state": [elem['finalStateType']['value']],
                    "object": elem['finalObject']['value']
                }
            else:
                if elem['finalStateType']['value'] not in stateMap[finalState]['state']:
                    stateMap[finalState]['state'].append(elem['finalStateType']['value'])
        else:
            if finalState not in stateMap:
                stateMap[finalState] = {
                    "state": [],
                    "object": elem['finalObject']['value']
                }
            else:
                pass
        
        if activity in activityMap:
            if firstState not in activityMap[activity]['firstState']:
                activityMap[activity]['firstState'].append(firstState)
            if finalState not in activityMap[activity]['finalState']:
                activityMap[activity]['finalState'].append(finalState)
        else:
            #activity初出時
            activityMap[activity] = {
                'firstState': [firstState],
                'finalState': [finalState]
            }

    activity_pair_list = []
    for pair in itertools.permutations(list(activityMap), 2):
        activity_pair_list.append(pair)

    routine = readRoutine('graph_state_list/routine_list.txt')
    activity_list = []
    for activity in routine:
        activity = activity.replace(' ', '_')
        activity = activity.lower()
        activity_list.append(getActivity(activity))

    for i in range(len(activity_list)-1):
        activity1 = activity_list[i]
        activity1_value = activityMap[activity1]
        activity2 = activity_list[i+1]
        activity2_value = activityMap[activity2]
        print([activity1, activity2])
        assert checkConsistency(activity1_value, activity2_value)
        update(activity1, activity2)
