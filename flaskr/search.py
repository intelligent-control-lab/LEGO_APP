


import os
import json
import numpy as np
import difflib
from flask import Blueprint, render_template, request, flash

bp = Blueprint('search', __name__)

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
        for subfolder in subfolders:
            subfolder_path = os.path.join(folder_path, subfolder)
            models_path = os.path.join(subfolder_path, 'models')
            task_graph_path = os.path.join(models_path, 'task_graph.json')
            stability_score_path = os.path.join(models_path, 'stability_score.npy')
            
            if os.path.exists(task_graph_path) and os.path.exists(stability_score_path):
                unique_brick_count = count_unique_brick_ids(task_graph_path)
                red_bricks_count = count_red_bricks(stability_score_path)
                
                if unique_brick_count <= target_brick_count and red_bricks_count == target_red_brick_count:
                    matching_folders.append(subfolder_path)
                    count += 1
                if count >= 10:
                    break
            else:
                print(f"Files missing in {subfolder_path}")
    return matching_folders

@bp.route('/', methods=['GET', 'POST'])
def search():
    matching_folders = None
    base_dir = '/Users/kareemsegizekov/Downloads/StableLego'  # Define base_dir here

    if request.method == 'POST':
        keyword = request.form.get('keyword')
        target_brick_count = int(request.form.get('target_brick_count'))
        target_red_brick_count = int(request.form.get('target_red_brick_count'))

        python_dict = {
            'Airplane': '02691156',
            'Trash_Can': '02747177',
            'Bag': '02773838',
            'Bin': '02801938',
            'Tub': '02808440',
            'Bed': '02818832',
            'Bench': '02828884',
            'Hut': '02843684',
            'Bookshelf': '02871439',
            'Bottle': '02876657',
            'Bowl': '02880940',
            'Bus': '02924116',
            'Drawer': '02933112',
            'Camera': '02942699',
            'Can': '02946921',
            'Hat': '02954340',
            'Car': '02958343',
            'Chair': '03001627',
            'Clock': '03046257',
            'Speaker': '03691459',
            'Table': '04379243',
            'Phone': '04401088',
            'Tower': '04460130',
            'Train': '04468005',
            'Boat': '04530566',
            'Washing_Machine': '04554684'
        }

        # Find the closest match to the keyword
        closest_matches = difflib.get_close_matches(keyword, python_dict.keys(), n=1, cutoff=0.6)
        if closest_matches:
            closest_keyword = closest_matches[0]
            folder_id = python_dict.get(closest_keyword)
            if folder_id:
                matching_folders = find_matching_folders(base_dir, folder_id, target_brick_count, target_red_brick_count)
        else:
            flash('Keyword not found in the dictionary.')

    return render_template('search.html', matching_folders=matching_folders)
