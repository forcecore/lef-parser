"""
Train a ML model to predict cells based on vias location

Name: Tri Minh Cao
Email: tricao@utdallas.edu
Date: October 2016
"""

import pickle
import random
import os
from def_parser import *
from lef_parser import *
import util
from sklearn.linear_model import LogisticRegression
import numpy as np

# idea: get 900 cells from each type
# separate all data into bins labeled by macro name (AND2, INVX1, etc.)
# when I train, I will select randomly samples from those bins
FEATURE_LEN = 9

def merge_data():
    random.seed(12345)
    num_cells_required = 900

    all_samples = []
    all_labels = []

    pickle_folder = "./training_data"
    pickle_files = os.listdir(pickle_folder)
    # print (pickle_files)
    for file in pickle_files:
        # pickle_file = "./training_data/c1355.def.pickle"
        pickle_file = os.path.join(pickle_folder, file)
        try:
            with open(pickle_file, 'rb') as f:
                dataset = pickle.load(f)
        except Exception as e:
            print('Unable to read data from', pickle_file, ':', e)
        all_samples.extend(dataset[0])
        all_labels.extend(dataset[1])

    all_dataset = (all_samples, all_labels)
    # pickle the merged data
    set_filename = "./merged_data/freepdk45_10_17_16.pickle"
    try:
        with open(set_filename, 'wb') as f:
            pickle.dump(all_dataset, f, pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        print('Unable to save data to', set_filename, ':', e)

    dataset = {}
    dataset['AND2X1'] = []
    dataset['INVX1'] = []
    dataset['INVX8'] = []
    dataset['NAND2X1'] = []
    dataset['NOR2X1'] = []
    dataset['OR2X1'] = []

    choices = [i for i in range(len(all_samples))]
    random.shuffle(choices)
    for idx in choices:
        features = all_samples[idx]
        label = all_labels[idx]
        if len(dataset[label]) < 900:
            dataset[label].append(features)
        cont = False
        for each_macro in dataset:
            if len(dataset[each_macro]) < 900:
                cont = True
        if not cont:
            break

    for each_macro in dataset:
        print (each_macro)
        print (len(dataset[each_macro]))

    # pickle the selected data
    set_filename = "./merged_data/selected_10_17_16.pickle"
    try:
        with open(set_filename, 'wb') as f:
            pickle.dump(dataset, f, pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        print('Unable to save data to', set_filename, ':', e)


def train_model():
    #################
    # CONSTANTS
    train_len = 5000
    feature_len = 9
    #################
    train_dataset = np.ndarray(shape=(train_len, feature_len),
                               dtype=np.float32)
    train_label = np.ndarray(train_len,
                             dtype=np.int32)
    current_size = 0
    num_selected = [0, 0, 0, 0, 0, 0]
    while current_size < train_len:
        choice = random.randrange(6)
        cur_label = num_to_label[choice]
        cur_idx = num_selected[choice]
        train_dataset[current_size, :] = np.array(dataset[cur_label][cur_idx],
                                                  dtype=np.int32)
        train_label[current_size] = choice
        current_size += 1
        num_selected[choice] += 1

    # shuffle the dataset

    train_dataset, train_label = util.randomize(train_dataset, train_label)

    test_dataset = train_dataset[4500:]
    test_label = train_label[4500:]
    train_dataset = train_dataset[:4500]
    train_label = train_label[:4500]
    # print (len(test_dataset))
    # print (len(test_label))
    # print (len(train_dataset))
    # print (len(train_label))

    # train a logistic regression model
    regr = LogisticRegression()
    X_train = train_dataset
    y_train = train_label

    X_test = test_dataset
    y_test = test_label

    regr.fit(X_train, y_train)
    score = regr.score(X_test, y_test)
    pred_labels = regr.predict(X_test)
    print(pred_labels[:100])
    print(score)

    # Save the trained model for later use
    filename = "./trained_models/logit_model_101716.pickle"
    try:
        with open(filename, 'wb') as f:
            pickle.dump(regr, f, pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        print('Unable to save data to', filename, ':', e)


def predict_cell(candidates, row, model, lef_data):
    """
    Use the trained model to choose the most probable cell from via groups.
    :param candidates: 2-via and 3-via groups that could make a cell
    :return: a tuple (chosen via group, predicted cell name)
    """
    margin = 350
    dataset = np.ndarray(shape=(len(candidates), FEATURE_LEN),
                         dtype=np.float32)
    for i in range(len(candidates)):
        each_group = candidates[i]
        left_pt = [each_group[0][0][0] - margin, CELL_HEIGHT * row]
        width = each_group[-1][0][0] - left_pt[0] + margin
        dataset[i, :] = image_data

    # Logistic Regression uses.
    X_test = dataset.reshape(dataset.shape[0], img_shape)

    result = model.decision_function(X_test)
    proba = model.predict_proba(X_test)
    print (result)
    # for each in result:
    #     print (sum(each))
    # print (proba)
    scores = []
    predicts = []
    for each_prediction in result:
        scores.append(max(each_prediction))
        predicts.append(np.argmax(each_prediction))
    best_idx = np.argmax(scores)
    return candidates[best_idx], predicts[best_idx]

# Main Class
if __name__ == '__main__':
    random.seed(12345)
    num_cells_required = 900

    #merge_data()

    # load data from selected pickle
    set_filename = "./merged_data/selected_10_17_16.pickle"
    try:
        with open(set_filename, 'rb') as f:
            dataset = pickle.load(f)
    except Exception as e:
        print('Unable to read data from', set_filename, ':', e)


    # build the numpy array
    label_to_num = {'AND2X1': 0, 'INVX1': 1, 'INVX8': 2, 'NAND2X1': 3,
                    'NOR2X1': 4, 'OR2X1': 5}

    num_to_label = {0: 'AND2X1', 1: 'INVX1', 2: 'INVX8', 3: 'NAND2X1',
                    4: 'NOR2X1', 5: 'OR2X1'}


    #######
    # DO SOME PREDICTION

    # We can load the trained model
    pickle_filename = "./trained_models/logit_model_101716.pickle"
    try:
        with open(pickle_filename, 'rb') as f:
            logit_model = pickle.load(f)
    except Exception as e:
        print('Unable to read data from', pickle_filename, ':', e)

    labels = {0: 'and2', 1: 'invx1', 2: 'invx8', 3: 'nand2', 4: 'nor2',
              5: 'or2'}
    cell_labels = {'AND2X1': 'and2', 'INVX1': 'invx1', 'NAND2X1': 'nand2',
                   'NOR2X1': 'nor2', 'OR2X1': 'or2', 'INVX8': 'invx8'}

    def_path = './libraries/layout_freepdk45/c432.def'
    def_parser = DefParser(def_path)
    def_parser.parse()
    scale = def_parser.scale

    lef_file = "./libraries/FreePDK45/gscl45nm.lef"
    lef_parser = LefParser(lef_file)
    lef_parser.parse()

    CELL_HEIGHT = int(float(scale) * lef_parser.cell_height)
    # print (CELL_HEIGHT)
    print ("Process file:", def_path)
    all_via1 = get_all_vias(def_parser, via_type="M2_M1_via")
    # print (all_via1)

    # sort the vias by row
    via1_sorted = sort_vias_by_row(def_parser.diearea[1], CELL_HEIGHT, all_via1)

    MAX_DISTANCE = 2280 # OR2 cell width, can be changed later

    components = util.sorted_components(def_parser.diearea[1], CELL_HEIGHT,
                                   def_parser.components.comps)

    num_rows = len(components)
    # process
    # print the sorted components
    correct = 0
    total_cells = 0
    predicts = []
    actuals = []
    # via_groups is only one row
    # for i in range(len(via1_sorted)):
    for i in range(3, 4):
        via_groups = group_via(via1_sorted[i], 3, MAX_DISTANCE)
        visited_vias = [] # later, make visited_vias a set to run faster
        cells_pred = []
        for each_via_group in via_groups:
            first_via = each_via_group[0][0]
            # print (first_via)
            if not first_via in visited_vias:
                best_group, prediction = predict_cell(each_via_group, i,
                                                      logit_model, lef_parser)
                print (best_group)
                print (labels[prediction])
                cells_pred.append(labels[prediction])
                for each_via in best_group:
                    visited_vias.append(each_via)
                    # print (best_group)
                    # print (labels[prediction])

        print (cells_pred)
        print (len(cells_pred))

        actual_comp = []
        actual_macro = []
        for each_comp in components[i]:
            actual_comp.append(cell_labels[each_comp.macro])
            actual_macro.append(each_comp.macro)
        print (actual_comp)
        print (len(actual_comp))

        # check predictions vs actual cells
        # for i in range(len(actual_comp)):
        #     if cells_pred[i] == actual_comp[i]:
        #         correct += 1
        num_correct, num_cells = predict_score(cells_pred, actual_comp)

        correct += num_correct
        total_cells += num_cells
        predicts.append(cells_pred)
        actuals.append(actual_comp)

        print ()

    print (correct)
    print (total_cells)
    print (correct / total_cells * 100)

