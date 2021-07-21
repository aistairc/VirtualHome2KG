#!/usr/bin/env python3
import os
import csv
import random
import rdflib
from SPARQLWrapper import SPARQLWrapper, JSON

def convert_name(table):
    result = []
    activity_class_map = {
        "就寝・起床": "BedTimeSleep",
        "飲食": "EatingDrinking",
        "飲食準備": "FoodPreparation",
        "整理・整頓": "HouseArrangement",
        "清掃・洗浄": "HouseCleaning",
        "衛生": "HygieneStyling",
        "娯楽": "Leisure",
        "仕事・学業": "Work",
        "身体活動": "PhysicalActivity",
        "その他": "Other"
    }
    for line in table:
        new_line = []
        for x in line:
            new_line.append(activity_class_map[x])
        result.append(new_line)
    return result


def add_start_end(sequence):
    tmp = ['start']
    tmp.extend(sequence)
    tmp.extend(['end'])
    return tmp


def create_ngram(sequence_list):
    ngram = {}
    for seq in sequence_list:
        for i in range(7):
            if seq[i] in ngram:
                values = ngram[seq[i]]
                if seq[i+1] in values.keys():
                    values[seq[i+1]] += 1
                else:
                    values[seq[i+1]] = 1
                ngram[seq[i]] = values
            else:
                tmp = {}
                tmp[seq[i+1]] = 1
                ngram[seq[i]] = tmp
    return ngram


def create_transition_probability(ngram):
    transition_probability = {}
    for current_activity in ngram:
        next_activities = ngram[current_activity]
        num = 0
        for na_key in next_activities:
            num += next_activities[na_key]
        probability = {}
        for na_key in next_activities:
            probability[na_key] = next_activities[na_key] / num
        transition_probability[current_activity] = probability
    return transition_probability


def markov_chain(transition_probability):
    current_activity = "start"
    activity_list = []
    for i in range(6):
        next_candidates = {}
        next_candidates = transition_probability[current_activity]

        keys = []
        values = []
        for x in next_candidates:
            keys.append(x)
            values.append(next_candidates[x])
        next_activity = random.choices(
            population=keys,
            weights=values
        )
        current_activity = next_activity[0]
        if current_activity == "end":
            break
        activity_list.append(current_activity)
    return activity_list


def get_activity_from_ontology(activity_type):
    result = None
    queryString = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX : <http://www.owl-ontologies.com/VirtualHome.owl#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        select ?activity ?label ?comment where { 
            ?activity a ?activityClass ;
                rdfs:label ?label ;
                rdfs:comment ?comment .
            ?activityClass rdfs:subClassOf :%s.
         } ORDER BY RAND() limit 1 
    """
    sparql = SPARQLWrapper("http://localhost:7200/repositories/VirtualHome2Kg")

    sparql.setQuery(queryString % activity_type)
    sparql.setReturnFormat(JSON)

    try :
        json = sparql.query().convert()
        bindings = json['results']['bindings']
        #result = bindings[0]["activity"]["value"]
        result = bindings[0]
    except  Exception as e:
        result = e
    return result

def export(routine_list):
     with open("graph_state_list/routine_list.txt", 'w') as f:
        f.write("%s\n" % ','.join(routine_list[0]))

# --------------------#

if __name__ == "__main__":
    cs_results = []
    with open("../dataset/lancers_task.csv", encoding="utf-8", newline="") as f:
        for cols in csv.reader(f, delimiter=","):
            cs_results.append(cols)
    # delete header
    cs_results.pop(0)

    # preprocess
    weekdays = []
    holidays = []
    for x in cs_results:
        weekdays.append(x[0:18])
        holidays.append(x[18:36])
    weekdays = convert_name(weekdays)
    holidays = convert_name(holidays)

    weekdays_morning = []
    weekdays_afternoon = []
    weekdays_evening = []
    holidays_morning = []
    holidays_afternoon = []
    holidays_evening = []
    for x in weekdays:
        weekdays_morning.append(add_start_end(x[0:6]))
        weekdays_afternoon.append(add_start_end(x[6:12]))
        weekdays_evening.append(add_start_end(x[12:18]))

    for x in holidays:
        holidays_morning.append(add_start_end(x[0:6]))
        holidays_afternoon.append(add_start_end(x[6:12]))
        holidays_evening.append(add_start_end(x[12:18]))

    sequence_list = weekdays_morning
    sequence_list.extend(weekdays_afternoon)
    sequence_list.extend(weekdays_evening)
    sequence_list.extend(holidays_morning)
    sequence_list.extend(holidays_afternoon)
    sequence_list.extend(holidays_evening)

    # Ngram
    ngram = create_ngram(sequence_list)
    transition_probability = create_transition_probability(ngram)
    routine_list = []
    for i in range(5):
        routine_list.append(markov_chain(transition_probability))

    # load vh2kg_ontology
    rdf_g = rdflib.Graph()
    rdf_g.parse("../ontology/vh2kg_ontology.ttl", format="ttl")

    # instanciation
    new_routine_list = []
    for routine in routine_list:
        new_routine = []
        for activity in routine:
            binding = get_activity_from_ontology(activity)
            new_routine.append(binding["label"]["value"])
        new_routine_list.append(new_routine)

    print(new_routine_list)

    # export
    export(new_routine_list)
