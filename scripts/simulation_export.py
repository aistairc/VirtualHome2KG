#!/usr/bin/env python3
import sys
sys.path.append('../simulation/')
sys.path.append('../dataset_utils/')
sys.path.append('../demo/')
from utils_demo import *
from sys import platform
from PIL import Image
import matplotlib.pyplot as plt
import json
import rdflib
import glob
import os
import re
import copy
import time
import numpy as np
import random
import cv2
import add_preconds
import evolving_graph.check_programs as check_programs
import evolving_graph.utils as utils
from unity_simulator.comm_unity import UnityCommunication

comm = UnityCommunication()

equivalent_class_name = {
    "food_bread": "breadslice",
    "freezer": "fridge",
    "coffe_maker": "coffeemaker",
    "pot": "coffeepot",
    "wall_clock": "clock",
    "home_office": "livingroom",
    "living_room": "livingroom",
    "couch": "sofa",
    "laptop": "computer",
    "newspaper": "magazine",
    "television": "tv",
    "remote_control": "remotecontrol",
    "carpet": "rug",
    "cd_player": "radio",
    "shower": "stall",
    "entrance_hall": "livingroom",
    "cleaning_bottle": "dishwashingliquid",
    "electrical_outlet": "powersocket",
    "dresser": "closet",
    "picture": "photoframe",
    "food_food": "pie",
    "lamp": "tablelamp",
    "groceries": "mincedmeat",
    "washing_machine": "washingmachine",
    "toilet_paper": "toiletpaper",
    "bathroom_cabinet": "bathroomcabinet",
    "tooth_paste": "toothpaste",
    "clothes_pants": "clothespants",
    "woman":  "character",
    "dining_room": "kitchen",
    "filing_cabinet": "cabinet",
    "kitchen_cabinet": "kitchencabinet",
    "basket_for_clothes": "clothespile",
    "sponge": "washingsponge",
    "dish_soap": "dishwashingliquid",
    "mop_bucket": "bucket",
    "rag": "towel",
    "cleaning_solution": "dishwashingliquid"
    }

unsupport_unity_exec_time = {
    "Wipe": 5.0,
    "PutOn": 10.0,
    "PutOff": 10.0,
    "Greet": 3.0,
    "Drop": 2.0,
    "Read": 1800.0,
    "Lie": 5.0,
    "Pour": 5.0,
    "Type": 10.0,
    "Watch": 7200.0,
    "Move": 5.0,
    "Wash": 10.0,
    "Squeeze": 5.0,
    "PlugIn": 5.0,
    "PlugOut": 5.0,
    "Cut": 5.0,
    "Eat": 1200.0,
    "Sleep": 21600.0,
    "Wake": 5.0
}

def get_activity_from_ontology(activity_type):
    qres = rdf_g.query("""
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX : <http://www.owl-ontologies.com/VirtualHome.owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
select ?activity where {
?activity rdfs:subClassOf :%s .
} ORDER BY RAND() limit 1 """ % activity_type)

    result = ""
    for row in qres:
        activity = "".join(row).replace("http://www.owl-ontologies.com/VirtualHome.owl#", "")
        arr = activity.split("_")
        arr[0] = arr[0].capitalize()
        activity = " ".join(arr)
        result = activity
    return result

def generate_list_of_steps(file_path, nodes):
    file = open(file_path, "r", encoding="utf-8")
    i = 0
    list_of_steps = []
    program_name = ""
    description = ""
    char = "<char0>"
    while True:
        line = file.readline()
        if line:
            line = line.replace("\n", "")
            if i == 0:
                program_name = line
            elif i == 1:
                description = line
            elif line.startswith("["):
                list_of_steps.append(line)
            else:
                pass
            i += 1
        else:
            break
    return program_name, description, list_of_steps

def add_routine(routines, category):
    #unexecutable = ["Take shower", "Take shoes off", "Wash teeth", "Wash face", "Dust", "Clean toilet", "Clean room", "Scrubbing living room tile floor is once week activity for me", "Clean mirror", "Play games", "Play on laptop", "Read on sofa"]
    unexecutable = []
    while True:
        activity_name = get_activity_from_ontology(category)
        if activity_name in unexecutable:
            continue
        results = [program for program in program_list if program["name"] == activity_name]
        if len(results) == 0:
            print("Nothing: " + activity_name)
        else:
            print("Success: " + activity_name)
            routines.append(results[0])
            break
    return routines, activity_name

def replace_class_name_of_preconds(preconds, equivalent_class_name):
    new_preconds = copy.deepcopy(preconds)
    for precond in new_preconds:
        key = [x for x in precond.keys()][0]
        values = precond[key]
        if type(values[0]) is not str :
            for value in values:
                if value[0] in equivalent_class_name:
                    value[0] = equivalent_class_name[value[0]]
        else:
            if values[0] in equivalent_class_name:
                values[0] = equivalent_class_name[values[0]]
    return new_preconds

def replace_class_name_of_script(script, equivalent_class_name):
    new_script = copy.deepcopy(script)
    result = []
    for line in new_script:
        for q in equivalent_class_name.keys():
            if q in line:
                line = line.replace(q, equivalent_class_name[q])
        result.append(line)
    return result

def delete_edge(g, from_id, relation):
    for edge in g["edges"]:
        if edge["from_id"] == from_id:
            g["edges"].remove(edge)
    return g

def free(g, to_id, relation):
    for edge in g["edges"]:
        if edge["to_id"] == to_id and edge["relation_type"] == "ON":
            g["edges"].remove(edge)
    return g

def update_precondition(g, preconds):
    unary_preconditions = {
        "is_on": "ON",
        "is_off": "OFF",
        "plugged": "PLUGGED_IN",
        "unplugged": "PLUGGED_OUT",
        "open": "OPEN",
        "closed": "CLOSED",
        "occupied": "ON",
        "sit": "SITTING",
        "sitting": "SITTING",
        "lying": "LYING",
        "free": "free"
    }
    binary_preconditions = {
        "inside": "INSIDE",
        "in": "ON",
        "location": "INSIDE",
        "facing": "FACING",
        "atreach": "CLOSE"
    }
    for precond in preconds:
        key = [x for x in precond.keys()][0]
        relation = None
        isBinary = False
        if key in unary_preconditions:
            relation = unary_preconditions[key]
        elif key in binary_preconditions:
            relation = binary_preconditions[key]
            isBinary = True
        else:
            print("nothing")
            return None
        values = precond[key]

        try:
            if isBinary:
                #print(values)
                from_obj = values[0]
                to_obj = values[1]
                from_id =  find_nodes(g, class_name=from_obj[0])[int(from_obj[1])-1]["id"]
                to_id =  find_nodes(g, class_name=to_obj[0])[int(to_obj[1])-1]["id"]
                g = delete_edge(g, from_id, relation)
                add_edge(g, from_id, relation, to_id)
            else:
                obj = find_nodes(g, class_name=values[0])[int(values[1])-1]
                if key == "free":
                    g = free(g, to_id=obj["id"], relation="ON")
                else:
                    obj["states"] = [relation]
                #print(obj)
            success, message = comm.expand_scene(g)
            print(success)
        except Exception as e:
            print(values)
            print(e)
    return g

def add_new_node(g, from_obj, to_obj, relation, max_id):
    try:
        add_node(g, {'class_name': from_obj[0], 
                           'category': 'placable_objects', 
                           'id': max_id, 
                           'properties': [], 
                           'states': []})
        to_node = find_nodes(g, class_name="livingroom")[0]
        add_edge(g, max_id, "INSIDE", to_node["id"])
        success, message = comm.expand_scene(g)
        print(success)
        print(message)
        print([from_obj, to_obj, relation, to_node])
    except Exception as e:
        print(e)
    return g

#実行できるように環境を初期化
def init_environment(g, scene, preconds):
    #トースターに刺さっているパンを削除
    for breadslice in find_nodes(g, class_name='breadslice'):
        g["nodes"].remove(breadslice)
        g = delete_edge(g, breadslice['id'], None)
    
    max_id = 1000
    for precond in preconds:
        key = [x for x in precond.keys()][0]
        
        #今の環境に追加されて無いオブジェクトが条件に入っている場合
        if key == 'location' or key == 'atreach':
            binary_preconditions = {"location": "INSIDE", "atreach": "CLOSE"}
            relation = binary_preconditions[key]
            values = precond[key]
            from_obj = values[0]
            to_obj = values[1]
            if len(find_nodes(g, class_name=from_obj[0])) == 0:
                g = add_new_node(g, from_obj, to_obj, relation, max_id)
                max_id += 1
                
        #前提条件にinsideがある場合（物をなにかの中に入れておく必要がある）
        elif key == 'inside':
            values = precond[key]
            from_obj = values[0]
            to_obj = values[1]
            g = precond_inside(g, from_obj, to_obj, max_id)
            max_id += 1
    return g

def precond_inside(g, from_obj, to_obj, max_id):
    from_class_name = from_obj[0]
    to_class_name = to_obj[0]
    try:
        box = find_nodes(g, class_name=to_class_name)[int(to_obj[1])-1]
        box["states"] = ["OPEN"]
        success, message = comm.expand_scene(g)
        if success:
            add_node(g, {'class_name': from_class_name, 
                               'category': 'placable_objects', 
                               'id': max_id, 
                               'properties': [], 
                               'states': []})
            add_edge(g, max_id, 'INSIDE', box["id"])
            success, message = comm.expand_scene(g)
            if success:
                box = find_nodes(g, class_name=to_class_name)[int(to_obj[1])-1]
                box["states"] = ["CLOSED"]
                success, message = comm.expand_scene(g)
                if success:
                    print("success")
                    return g
                else:
                    print("[error] box CLOSED: " + message)
            else:
                print("[error] add_node: " + message)
        else:
            print("[error] box OPEN: " + message)
    except Exception as e:
        print(e)
    return g

def check_recovery(script, message):
    flag = False
    if 'is not close to' in message:
        m = re.search(r'\[\d+\]', message)
        cnt = m.group().replace('[','')
        cnt = cnt.replace(']','')
        m2 = re.search(r'\[\w+\]', new_script[int(cnt)-1])
        action = m2.group().replace('[', '')
        action = action.replace(']', '')
        tmp_line = copy.deepcopy(new_script[int(cnt)-1])
        additional_action  = tmp_line.replace(action, "Walk")
        #additional_action = new_script[int(cnt)-1].replace(action, "Walk")
        #script[int(cnt)-1:1] = [additional_action]
        script.insert(int(cnt)-1,additional_action)
        flag = True
    return flag, script

def update_node_states(pre_graph, current_graph, executed_script, i):
    try:
        obj_id = None
        executed_script_line = [re.sub("\[\d+\]","",x.__str__()).strip() for x in executed_script][i-1]
        m = re.search(r'<\w+>', executed_script_line)
        if m is not None:
            class_name = m.group().replace('<', '')
            class_name = class_name.replace('>', '')
            m = re.search(r'\(\d+\)', executed_script_line)
            obj_id =m.group().replace('(', '')
            obj_id = obj_id.replace(')', '')
       
        
        #character
        char_id =  find_nodes(g, class_name='character')[0]["id"]

        new_graph= copy.deepcopy(pre_graph)
        for x_id in [char_id, obj_id]:
            if obj_id is None:
                break
            #該当ノードの現在のstates
            current_node_states = []
            for node in current_graph["nodes"]:
                if node["id"] == int(x_id):
                    current_node_states = node["states"]
                    print(current_node_states)
                    break

            #該当ノードの前回の状態
            for node in new_graph["nodes"]:
                if node["id"] == int(x_id):
                    #この中で更新処理する
                    node["states"] = current_node_states
                    break
        
    except Exception as e:
        print(e)
    
    return new_graph

scene = 4
scene_graph = "TrimmedTestScene" + str(scene) + "_graph"
executable_program_path = "../dataset/programs_processed_precond_nograb_morepreconds/executable_programs/" + scene_graph + "/*/*.txt"
executable_program_list = []
for file_path in glob.glob(executable_program_path):
    executable_program_list.append(file_path.replace("../dataset/programs_processed_precond_nograb_morepreconds/executable_programs/" + scene_graph + "/", ""))

print("Load HomeOntology")
rdf_g = rdflib.Graph()
rdf_g.parse("../ontology/HomeOntology_without_individuals.ttl", format="ttl")

# set character
print("set scene and character")
program_list = []
comm.reset(scene)
comm.add_character('chars/Female2')

# load environment
print("Load environment")
success, g = comm.environment_graph()

nodes = g["nodes"]
edges = g["edges"]
max_id = nodes[len(nodes)-1]["id"]

# load activity data
print("load activity data")
data_path = "../dataset/programs_processed_precond_nograb_morepreconds/withoutconds/*/*.txt"
program_list = []
for file_path in glob.glob(data_path):
    file_name = file_path.replace("../dataset/programs_processed_precond_nograb_morepreconds/withoutconds/", "")
    if file_name in executable_program_list:
        program_name, description, list_of_steps = generate_list_of_steps(file_path, nodes)
        program_list.append({
            "file_name":file_name,
            "name": program_name,
            "description": description,
            "list_of_steps": list_of_steps
        })

results = []
routines = []
#routines = add_routine(routines, "EatingDrinking")
routines, activity_name = add_routine(routines, sys.argv[1])

script = []
scriptsize_list = []
for program in routines:
    script.extend(program["list_of_steps"])
    scriptsize_list.append(len(program["list_of_steps"]))
print(script)

preconds = add_preconds.get_preconds_script(script).printCondsJSON()
new_preconds = replace_class_name_of_preconds(preconds, equivalent_class_name)

g = init_environment(g, scene, new_preconds)
g = update_precondition(g, new_preconds)

new_script = replace_class_name_of_script(script, equivalent_class_name)

executable_program = []
for x in new_script:
    executable_program.append("<char0> " + x)

close = False
while not close:
    info = check_programs.check_script(new_script, new_preconds, graph_path=None, inp_graph_dict=g)
    message, final_state, graph_state_list, graph_dict, id_mapping, info, helper, executed_script = info

    if "Script is not executable" in message:
        flag, new_script = check_recovery(new_script, message)
        if flag:
            print("script is modified")
            executable_program = []
            for x in new_script:
                executable_program.append("<char0> " + x)
        else:
            break
    else:
        close = True
print(message)

executed_program = []
for x in executed_script:
    executed_program.append("<char0> " + re.sub("\[\d+\]","",x.__str__()).strip())
print(executed_program)

new_graph_state_list = []
success, g = comm.environment_graph();
new_graph_state_list.append(copy.deepcopy(g))
time_list = []
i = 0
for (line, line2) in zip(executable_program, new_script):
    i += 1
    program = [line]
    m = re.search(r'\[.+\]', line)
    action = m.group().replace('[', '')
    action = action.replace(']', '')
    start = time.time()
    if action in [x for x in unsupport_unity_exec_time.keys()]:
        #unityがsupportしてないaction
        try:
            program = [line2]
            print(program)
            g = update_node_states(new_graph_state_list[i-1], graph_state_list[i], executed_script, i)
            new_graph_state_list.append(copy.deepcopy(g))
        except Exception as e:
            print("Error")
            print(e)
            break
    else:
        try:
            success, message = comm.render_script(script=program,
                                      processing_time_limit=300,
                                      find_solution=True,
                                      #image_width=320,
                                      #image_height=240,  
                                      #skip_animation=False,
                                      recording=True,
                                      gen_vid=False,
                                      #save_scene_states=True,
                                      #file_name_prefix='FoodPreparation',
                                      frame_rate=25
                                     )
            success, g = comm.environment_graph()
            print(str(success) + ": " + str(program))
            g = update_node_states(g, graph_state_list[i], executed_script, i)
            new_graph_state_list.append(copy.deepcopy(g))
        except Exception as e:
            print(e)
            break
            
    if action in [x for x in unsupport_unity_exec_time.keys()]:
        time_list.append(unsupport_unity_exec_time[action])
    else:
        time_list.append(time.time() - start)

os.mkdir("graph_state_list/" + activity_name)
state_cnt = 0
for graph_state in new_graph_state_list:
    state_cnt += 1
    file_path = "graph_state_list/" + activity_name + "/activityList-graph-state-" + '{0:03d}'.format(state_cnt) + ".json"
    with open(file_path, 'w') as outfile:
        json.dump(graph_state, outfile)

tmp_executable_program = []
program_cnt = 0
i = 0
for scriptsize in scriptsize_list:
    i += 1
    tmp_executable_program = executed_program[program_cnt:(program_cnt+scriptsize)]
    with open("graph_state_list/" + activity_name + "/activityList-program-" + '{0:03d}'.format(i)  + ".txt", 'w') as f:
        for s in tmp_executable_program:
            f.write("%s\n" % s)
    program_cnt = (program_cnt + scriptsize + 1)

j = 0
for activity in routines:
    j += 1
    with open("graph_state_list/" + activity_name + "/program-description-" + '{0:03d}'.format(j)  + ".txt", 'w') as f:
        f.write("%s\n" % activity["name"])
        f.write("%s\n" % activity["description"])

time_list = [str(time) for time in time_list]
duration = "\n".join(time_list)
with open("graph_state_list/" + activity_name + "/duration.txt", 'w') as f:
    f.write(duration)
