


import os
import json
import numpy as np
import difflib
import time
import random
import shutil
from flask import Blueprint, render_template, request, flash
import spacy

import rospy
from std_msgs.msg import Int64

bp = Blueprint('search', __name__)
matching_folders = None
build_folders = None
assembly_task = 0
request_obj = "Heart"

def count_unique_brick_ids(task_graph_path):
    try:
        with open(task_graph_path, 'r') as file:
            data = json.load(file)
            unique_brick_ids = set(data.keys())
            unique_brick_count = len(unique_brick_ids)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        unique_brick_count = 0  # or some default value
        print(f"Error reading {task_graph_path}: {e}")
    return unique_brick_count

def count_red_bricks(stability_score_path):
    try:
        stability_scores = np.load(stability_score_path, allow_pickle=True)
        red_bricks_count = np.sum(stability_scores == 1)
    except (FileNotFoundError, IOError) as e:
        red_bricks_count = 0  # or some default value
        print(f"Error reading {stability_score_path}: {e}")
    return red_bricks_count

def find_matching_folders(base_dir, folder_id, target_brick_count, target_red_brick_count):
    matching_folders = []
    folder_path = os.path.join(base_dir, folder_id)
    if os.path.isdir(folder_path):
        subfolders = [f.name for f in os.scandir(folder_path) if f.is_dir()]
        count = 0
        
        save_to_dir = "./flaskr/static/img/"
        files = os.listdir(save_to_dir)
        for file in files:
            file_path = os.path.join(save_to_dir, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        
        random.shuffle(subfolders)
        for subfolder in subfolders:
            subfolder_path = os.path.join(folder_path, subfolder)
            models_path = os.path.join(subfolder_path, 'models')
            task_graph_path = os.path.join(models_path, 'task_graph.json')
            stability_score_path = os.path.join(models_path, 'stability_score.npy')
            
            if os.path.exists(task_graph_path) and os.path.exists(stability_score_path):
                unique_brick_count = count_unique_brick_ids(task_graph_path)
                red_bricks_count = count_red_bricks(stability_score_path)
                
                if unique_brick_count <= target_brick_count and red_bricks_count <= target_red_brick_count:
                    original_vis_img_dir = subfolder_path + "/models/vis.png"
                    vis_img_dir = "/static/img/" + str(count) + ".png"
                    shutil.copy(original_vis_img_dir, save_to_dir + str(count) + ".png")
                    matching_folders.append({"dir":subfolder_path, "img_dir":vis_img_dir})
                    count += 1
                    if(count >= 5):
                        break
            else:
                print(f"Files missing in {subfolder_path}")
    return matching_folders

@bp.route('/', methods=['GET', 'POST'])
def search():
    global matching_folders
    global build_folders
    global assembly_task # 0:human, 1: heart, 2:gate, 3: chair, 4:mfi, 5:table
    global request_obj

    start_task_pub = rospy.Publisher('/yk_destroyer/start_task', Int64, queue_size=1)
    assembly_task_pub = rospy.Publisher('/yk_destroyer/assembly_task', Int64, queue_size=1)
    task_type_pub = rospy.Publisher('/yk_destroyer/task_type', Int64, queue_size=1)
    base_dir = '/home/mfi/repos/ros1_ws/src/ruixuan/StableLegoData/'  # Define base_dir here

    start_task = 0 # 1: executing 0: idle
    task_type = 1 # 1: assemble, 0: disassemble

    if request.method == 'POST':
        if("Build Lego" in request.form):
            request_obj = request.form.get("Build Lego")
            obj_dir = base_dir + "robot_tasks/" + request_obj
            shutil.copy(obj_dir + "/task_graph.json", "./flaskr/static/robot_tasks/task_graph.json")
            shutil.copy(obj_dir + "/vis.png", "./flaskr/static/robot_tasks/vis.png")
            build_folders = [{"dir": obj_dir, "img_dir": '/static/robot_tasks/vis.png'}]
            if("Preview" in request.form):
                pass
            elif("Build" in request.form):
                print("Build", request_obj)
                if(request_obj == "Man"):
                    assembly_task = 0
                elif(request_obj == "Heart"):
                    assembly_task = 1
                elif(request_obj == "Gate"):
                    assembly_task = 2
                elif(request_obj == "Chair"):
                    assembly_task = 3
                elif(request_obj == "MFI"):
                    assembly_task = 4
                elif(request_obj == "Table"):
                    assembly_task = 5
                start_task = 1
                task_type = 1
            elif("Disassemble" in request.form):
                print("Disassemble", request_obj, assembly_task)
                start_task = 1
                task_type = 0
        else:
            matching_folders = None
            keyword = request.form.get('keyword')
            target_brick_count = int(request.form.get('target_brick_count'))
            target_red_brick_count = 0

            python_dict = {
                'airplane': '02691156',
                'trash can': '02747177',
                'bag': '02773838',
                'bin': '02801938',
                'tub': '02808440',
                'bed': '02818832',
                'bench': '02828884',
                'hut': '02843684',
                'bookshelf': '02871439',
                'bottle': '02876657',
                'bowl': '02880940',
                'bus': '02924116',
                'drawer': '02933112',
                'camera': '02942699',
                'can': '02946921',
                'hat': '02954340',
                'car': '02958343',
                'chair': '03001627',
                'clock': '03046257',
                'speaker': '03691459',
                'table': '04379243',
                'phone': '04401088',
                'tower': '04460130',
                'train': '04468005',
                'boat': '04530566',
                'washing machine': '04554684'
            }
            
            # Find the closest match to the keyword
            # closest_matches = difflib.get_close_matches(keyword, python_dict.keys(), n=1, cutoff=0.6)

            nlp = spacy.load("en_core_web_lg") # python3 -m spacy download en_core_web_lg
            max_score = 0
            keyword_tokens = nlp(keyword)
            for k in python_dict.keys():
                tmp_tokens = nlp(k)
                sim = keyword_tokens.similarity(tmp_tokens)
                if(sim > max_score):
                    max_score = sim
                    closest_keyword = k
            print("Input keyword:", keyword)
            if 1:#closest_matches:
                print("Interpreted keyword:", closest_keyword)
                folder_id = python_dict.get(closest_keyword)
                if folder_id:
                    matching_folders = find_matching_folders(base_dir, folder_id, target_brick_count, target_red_brick_count)
            else:
                print("No available designs!")
                flash('Keyword not found in the dictionary.')
    
    assembly_task_pub.publish(assembly_task)
    task_type_pub.publish(task_type)
    start_task_pub.publish(start_task)
    time.sleep(0.5)
    start_task_pub.publish(0)

    return render_template('search.html', matching_folders=matching_folders, build_folders=build_folders)
