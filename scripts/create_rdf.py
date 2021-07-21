#!/usr/bin/env python3
import IPython.display
import sys
import json
from rdflib import *
from rdflib.collection import Collection
import glob
import os
import re


def getObjectName(line):
    #stepの行からすべてのobjectを抽出し、リストで返す
    result = []
    m = re.search(r'<.+>', line)
    if m is None:
        pass
    else:
        class_name = m.group()
        if "(" in class_name:
            #複数のobject
            class_name_list = re.split(r'\(\d+\)',class_name)
            for cn in class_name_list:
                cn = cn.replace("<","")
                cn = cn.replace(">","")
                cn = cn.strip()
                result.append(cn)
        else:
            #単一のobject
            class_name = class_name.replace("<","")
            class_name = class_name.replace(">","")
            class_name = class_name.strip()
            result.append(class_name)
        return result


def getActionName(line):
    m = re.search(r'\[.+\]', line)
    if m is not None:
        action = m.group()
        action = action.replace("[","")
        action = action.replace("]","")
        action = action.strip()
        return action
    else:
        assert "there is no action"


def getObjectId(line):
    result = []
    m = re.search(r'\(.+\)', line)
    if m is not None:
        id = m.group()
        if "(" in id:
            #複数のobject
            id_list = re.split(r'<.+>', id)
            for d in id_list:
                d = d.replace("(","")
                d = d.replace(")","")
                d = d.strip()
                result.append(d)
        else:
            result.append(id)
    else:
        assert "there is no ID"
    return result


def getActionResourceList(g, list_of_steps, action_id, activity_name, duration_list):
    base = Namespace("http://example.org/virtualhome2kg/ontology/")
    ho = Namespace("http://www.owl-ontologies.com/VirtualHome.owl#")
    time = Namespace("http://www.w3.org/2006/time#")
    action_list = []
    for (step, duration) in zip(list_of_steps, duration_list):
        step = step.replace("<char0>","").strip()
        object_list = getObjectName(step)
        action = getActionName(step)
        object_id_list = getObjectId(step)

        steptype = None
        if action in action_name_dic:
            print(action)
            steptype = action_name_dic[action]
        else:
            steptype = action.capitalize()

        action = action.lower()
        action = action + str(action_id)
        action_r = base[action + "_" + activity_name]

        # actionリソースのトリプル
        g.add((action_r, RDF.type, base[steptype]))
        g.add((action_r, base.actionNumber, Literal(action_id, datatype=XSD.int)))
        duration_r = base["time_" + action + "_" + activity_name]
        g.add((duration_r, RDF.type, time.Duration))
        g.add((duration_r, time.numericDuration, Literal(duration, datatype=XSD.decimal)))
        g.add((duration_r, time.unitType, time.unitSecond))
        g.add((action_r, time.hasDuration, duration_r))
        
        #初出action
        if (base[steptype], None, None) not in g:
            g.add((base[steptype], RDF.type, OWL.Class))
            g.add((base[steptype], RDFS.subClassOf, base.Action))

        #add object to action
        try:
            for (obj, obj_id) in zip(object_list, object_id_list):
                g.add((action_r, ho.object, base[obj + obj_id + "_" + scene]))
        except:
            print("object is None")
        

        if len(action_list) > 0:
            g.add((action_list[action_id-1], base.nextAction, action_r))
            g.add((action_r, base.previousAction, action_list[action_id-1]))
        action_list.append(action_r)
        action_id += 1
    return g, action_list


def getCharNode(nodes):
    result = None
    for node in nodes:
        if node['class_name'] == 'character':
            result = node
            break
    return result


def createObjectState(g, node, state_cnt, activity_name):
    base = Namespace("http://example.org/virtualhome2kg/ontology/")
    x3do = Namespace("https://www.web3d.org/specifications/X3dOntology4.0#")
    affordance_instances = ["CAN_OPEN", "CUTTABLE", "DRINKABLE", "EATABLE", "GRABBABLE", "HANGABLE", "LIEABLE", "LOOKABLE", "MOVABLE", "POURABLE", "READABLE", "SITTABLE"]
    object_property_instances = ["CREAM", "HAS_PAPER", "HAS_PLUG", "HAS_SWITCH", "PERSON", "RECIPIENT", "SURFACE"]
    
    id = node['id']
    class_name = node['class_name']
    category = node['category']
    node_properties = node['properties']
    node_states = node['states']
    bounding_box = node['bounding_box']
    
    obj_state_r = base['state' + str(state_cnt) + '_' + class_name + str(id) + "_" + activity_name]
    g.add((obj_state_r, RDF.type, base.State))
    
    g.add((obj_state_r, base.isStateOf, base[class_name + str(id)]))
    
    for vh_property in node_properties:
        if vh_property in affordance_instances:
            #Affordance
            g.add((obj_state_r, base.affordance, base[vh_property]))
        elif vh_property in object_property_instances:
            #Attribute
            g.add((obj_state_r, base.attribute, base[vh_property]))

    for node_state in node_states:
        #nodeが持つstateの値をStateクラスのインスタンスとして作成
        if (base[node_state], None, None) not in g:
            g.add((base[node_state], RDF.type, base.StateType))

        g.add((obj_state_r, base.state, base[node_state]))

    #bounding_box
    if bounding_box is not None:
        shape = base['shape_state' + str(state_cnt) + '_' + class_name + str(id) + '_' + activity_name]
        bbox_center = BNode()
        bbox_size = BNode()
        c_list = []
        s_list = []
        for c in bounding_box['center']:
            c_list.append(Literal(c, datatype=XSD.double))

        for s in bounding_box['size']:
            s_list.append(Literal(s, datatype=XSD.double))

        g.add((bbox_center, RDF.type, x3do.SFVec3f))
        g.add((bbox_size, RDF.type, x3do.SFVec3f))
        Collection(g, bbox_center, c_list)
        Collection(g, bbox_size, s_list)

        g.add((shape, RDF.type, x3do.Shape))
        g.add((shape, x3do.bboxCenter, bbox_center))
        g.add((shape, x3do.bboxSize, bbox_size))
        g.add((obj_state_r, base.bbox, shape))
    
    return g, obj_state_r


def getPreObjectState(g, state_cnt, class_name, id, activitiy_name):
    base = Namespace("http://example.org/virtualhome2kg/ontology/")
    pre_obj_state_r = base['state' + str(state_cnt-1) + '_' + class_name + str(id) + "_" + activitiy_name]
    #前の状態があるか
    if (pre_obj_state_r, None, None) in g:
        #前の状態がある
        pass
    else:
        #前の状態がないということは、前の状態は「前の前」の状態（あるいはもっと前）と同じ
        pre_cnt=1
        while True:
            #前の状態が見つかるまで探す
            pre_cnt+=1
            #print([state_cnt, pre_cnt, class_name])
            pre_obj_state_r = base['state' + str(state_cnt-pre_cnt) + '_' + class_name + str(id) + "_" + activitiy_name]
            if (pre_obj_state_r, None, None) in g:
                break
    return pre_obj_state_r


def createObjectAndSituation(g, graph_state_list, action_list, state_cnt, activity_name, scene):
    init_state_num = state_cnt
    base = Namespace("http://example.org/virtualhome2kg/ontology/")
    ho = Namespace("http://www.owl-ontologies.com/VirtualHome.owl#")
    x3do = Namespace("https://www.web3d.org/specifications/X3dOntology4.0#")
    for state in graph_state_list:
        nodes = state['nodes']
        edges = state['edges']
        home_situation_r = base["home_situation" + str(state_cnt) + "_" + activity_name]
        g.add((home_situation_r, RDF.type, base.Situation))
        #nodes
        for node in nodes:
            id = node['id']
            class_name = node['class_name']
            node_properties = node['properties']
            node_states = node['states']
            
            obj_r = base[class_name + str(id) + "_" + scene]
            if (obj_r, None, None) not in g:
                g.add((obj_r, RDF.type, base[class_name]))
                g.add((obj_r, RDFS.label, Literal(class_name)))
                g.add((obj_r, DCTERMS.identifier, Literal(str(id))))
                #ObjectType
                if (base.class_name, None, None) not in g:
                    g.add((base[class_name], RDF.type, OWL.Class))
                    g.add((base[class_name], RDFS.subClassOf, base.Object))
            
            if state_cnt == 0:
                #全objectのstateを作成
                g, obj_state_r = createObjectState(g, node, state_cnt, activity_name)
                g.add((obj_state_r, base.partOf, home_situation_r))
            
            else:
                diff_flag = False
                pre_obj_state_r = getPreObjectState(g, state_cnt, class_name, id, activity_name)

                '''
                    前の状態との比較開始
                '''
                #afford比較
                pre_obj_state_afford_list = [o.replace(base,'') for s, p, o in g.triples((pre_obj_state_r,  base.afford, None))]
                for afford in pre_obj_state_afford_list:
                    if afford not in node_properties:
                        diff_flag = True
                        break
                
                #afford比較
                if diff_flag == False:
                    for afford in node_properties:
                        if afford not in pre_obj_state_afford_list:
                            diff_flag = True
                            break
                
                #state比較
                if diff_flag == False:
                    pre_obj_state_state_list = [o.replace(base,'') for s, p, o in g.triples((pre_obj_state_r,  base.state, None))]
                    for pre_state in  pre_obj_state_state_list:
                        if pre_state not in node_states:
                            diff_flag = True
                            break
                            
                    if diff_flag == False:
                        for node_state in  node_states:
                            if node_state not in pre_obj_state_state_list:
                                diff_flag = True
                                break
                
                #bbox比較
                if diff_flag == False:
                    if (pre_obj_state_r, base.bbox, None) in g:
                        pre_obj_state_shape =  [x for x in g.objects(pre_obj_state_r, base.bbox)][0]
                        pre_obj_state_bboxCenter = [x for x in g.objects(pre_obj_state_shape, x3do.bboxCenter)][0]
                        pre_obj_state_x = [x for x in g.objects(pre_obj_state_bboxCenter, RDF.first)][0]
                        pre_obj_state_x_rest = [x for x in g.objects(pre_obj_state_bboxCenter, RDF.rest)][0]
                        pre_obj_state_y = [y for y in g.objects(pre_obj_state_x_rest, RDF.first)][0]
                        pre_obj_state_y_rest = [y for y in g.objects(pre_obj_state_x_rest, RDF.rest)][0]
                        pre_obj_state_z = [z for z in g.objects(pre_obj_state_y_rest, RDF.first)][0]
                        if node['bounding_box']['center'] != [pre_obj_state_x.value, pre_obj_state_y.value, pre_obj_state_z.value]:
                            diff_flag = True
                            print("state_cnt:" + str(state_cnt) + " " + class_name)
                        
                '''
                    前の状態との比較終了
                '''  
                
                if diff_flag == False:
                    #前の状態と同じ
                    g.add((pre_obj_state_r, base.partOf, home_situation_r))
                else:
                    #前の状態と違う
                    g, obj_state_r = createObjectState(g, node, state_cnt, activity_name)
                    g.add((obj_state_r, base.partOf, home_situation_r))
                    g.add((pre_obj_state_r, base.nextState, obj_state_r))
        
        #edges
        for edge in edges:
            from_id = edge["from_id"]
            to_id = edge["to_id"]
            if from_id == to_id:
                continue
            relation_type = edge["relation_type"].lower()
            from_obj_r = [x for x in g.subjects(DCTERMS.identifier, Literal(str(from_id)))][0]
            from_class_name = [x for x in g.objects(from_obj_r, RDFS.label)][0]
            from_obj_state_r = base['state' + str(state_cnt) + '_' + from_class_name + str(from_id) + '_' + activity_name]
            #前の状態がない場合、更に前の状態を取得
            if (from_obj_state_r, None, None) not in g:
                from_obj_state_r = getPreObjectState(g, state_cnt, from_class_name, from_id, activity_name)
            
            #shapeを取得
            if (from_obj_state_r, base.bbox, None) in g:
                from_shape_r = [x for x in g.objects(from_obj_state_r, base.bbox)][0]
            else:
                from_shape_r = base['shape_state' + str(state_cnt) + '_' + from_class_name + str(from_id) + '_' + activity_name]
            
            to_obj_r = [x for x in g.subjects(DCTERMS.identifier, Literal(str(to_id)))][0]
            to_class_name = [x for x in g.objects(to_obj_r, RDFS.label)][0]
            to_obj_state_r = base['state' + str(state_cnt) + '_' + to_class_name + str(to_id) + '_' + activity_name]
           #前の状態がない場合、更に前の状態を取得
            if (to_obj_state_r, None, None) not in g:
                to_obj_state_r = getPreObjectState(g, state_cnt, to_class_name, to_id, activity_name)
            
            #shapeを取得
            if (to_obj_state_r, base.bbox, None) in g:
                to_shape_r = [x for x in g.objects(to_obj_state_r, base.bbox)][0]
            else:
                to_shape_r = base['shape_state' + str(state_cnt) + '_' + to_class_name + str(to_id) + '_' + activity_name]
                
            g.add((from_shape_r,  base[relation_type], to_shape_r))
        
        state_cnt += 1
    
    i = 0
    for action_r in action_list:
        before_home_situation_r = base["home_situation" + str(init_state_num + i) + '_' + activity_name]
        after_home_situation_r = base["home_situation" + str(init_state_num + i+1) + '_' + activity_name]
        g.add((action_r, base.situationBeforeAction, before_home_situation_r))
        g.add((action_r, base.situationAfterAction, after_home_situation_r))
        g.add((before_home_situation_r, base.nextSituation, after_home_situation_r))
        i += 1
    
    return g, state_cnt


def create_rdf(graph_state_list, program_description, routines_program, scene, duration_list):
    base = Namespace("http://example.org/virtualhome2kg/ontology/")
    ho = Namespace("http://www.owl-ontologies.com/VirtualHome.owl#")
    x3do = Namespace("https://www.web3d.org/specifications/X3dOntology4.0#")
    time = Namespace("http://www.w3.org/2006/time#")
    g = Graph()
    g.bind("ex", base)
    g.bind("ho", ho)
    g.bind("x3do", x3do)
    g.bind("owl", OWL)
    g.bind("time", time)
    
    init_state = graph_state_list[0]
    nodes = init_state["nodes"]
    edges = init_state["edges"]
    
    #character
    char_node = getCharNode(nodes)
    char_class_name = char_node['class_name']
    char_id = char_node['id']
    char_r = base[char_class_name + str(char_id)]
    g.add((char_r, RDF.type, base.Character))
    g.add((char_r, RDFS.label, Literal(char_class_name)))
    g.add((char_r, DCTERMS.identifier, Literal(str(char_node['id']))))
    
    #activity
    id = 0
    state_cnt = 0
    
    activity_name = program_description["name"].lower().replace(" ","_") + str(id) + "_" + scene
    activity_r = base[activity_name]
    g.add((activity_r, RDFS.label, Literal(program_description["name"])))
    g.add((activity_r, RDFS.comment, Literal(program_description["description"])))
    g.add((activity_r, RDF.type, ho[program_description["name"].lower().replace(" ","_")]))

    #action関係
    action_id = id
    g, action_list = getActionResourceList(g, routines_program, action_id, activity_name, duration_list)

    for action_r in action_list:
        g.add((activity_r, base.action, action_r))
    #action関係終了

    #create objects and its situations
    g, state_cnt = createObjectAndSituation(g, graph_state_list, action_list, state_cnt, activity_name, scene)
            
    
    #Activity
    g.add((char_r, base.activity, activity_r))
    g.add((activity_r, base.agent, char_r))
    scene_r = base[scene]
    g.add((scene_r, RDF.type, base.VirtualHome))
    g.add((activity_r, base.virtualHome, scene_r))
    
    output_path = "graph_state_list/virtualhome2kg-" + folder.replace(" ", "_") + ".ttl"
    g.serialize(destination=output_path, format="turtle")

# ------ #

if __name__ == "__main__":
    action_name_dic = {
        'LOOKAT': 'LookAt',
        'PLUGIN': 'PlugIn',
        'PLUGOUT': 'PlugOut',
        'POINTAT': 'PointAt',
        'PUTBACK': 'PutBack',
        'STANDUP': 'StandUp',
        'TURNTO': 'TurnTo',
        'PUTOBJBACK': 'PutObjBack',
        'SWITCHOFF': 'SwitchOff',
        'SWITCHON': 'SwitchOn',
        'WAKEUP': 'WakeUp'
    }

    folder = sys.argv[1]

    # load description of activity
    program_description_path = "graph_state_list/" + folder + "/program-description-001.txt"
    program_description = {}
    input_file = open(program_description_path, "r")
    name_desc = []
    for line in input_file:
        name_desc.append(line.strip())
    input_file.close()
    program_description = {
        "name": name_desc[0],
        "description": name_desc[1]
    }
    print(program_description)

    # load activity
    routines_program_path = "graph_state_list/" + folder + "/activityList-program-001.txt"
    routines_program = []
    input_file = open(routines_program_path, "r")
    for line in input_file:
        routines_program.append(line.strip())
    input_file.close()

    # load graph state
    graph_state_path = "graph_state_list/" + folder + "/activityList-graph-state-*.json"
    graph_state_list = []
    for file_path in sorted(glob.glob(graph_state_path)):
        with open(file_path) as f:
            json_input = json.load(f)
            graph_state_list.append(json_input)

    # load duration
    duration_path = "graph_state_list/" + folder + "/duration.txt"
    duration_list = []
    input_file = open(duration_path, "r")
    for line in input_file:
        duration_list.append(line.strip())
    input_file.close()

    scene = 'scene5'
    create_rdf(graph_state_list, program_description, routines_program, scene, duration_list)
