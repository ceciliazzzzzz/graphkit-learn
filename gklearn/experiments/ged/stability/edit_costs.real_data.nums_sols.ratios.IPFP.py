#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct  20 11:48:02 2020

@author: ljia
"""
# This script tests the influence of the ratios between node costs and edge costs on the stability of the GED computation, where the base edit costs are [1, 1, 1, 1, 1, 1].

import os
import multiprocessing
import pickle
import logging
from gklearn.ged.util import compute_geds
import time
from utils import get_dataset, set_edit_cost_consts
import sys
from group_results import group_trials, check_group_existence, update_group_marker


def xp_compute_ged_matrix(dataset, ds_name, num_solutions, ratio, trial):

	save_file_suffix = '.' + ds_name + '.num_sols_' + str(num_solutions) + '.ratio_' + "{:.2f}".format(ratio) + '.trial_' + str(trial)

	# Return if the file exists.
	if os.path.isfile(save_dir + 'ged_matrix' + save_file_suffix + '.pkl'):
		return None, None

	"""**2.  Set parameters.**"""

	# Parameters for GED computation.
	ged_options = {'method': 'IPFP',  # use IPFP huristic.
				   'initialization_method': 'RANDOM',  # or 'NODE', etc.
				   # when bigger than 1, then the method is considered mIPFP.
				   'initial_solutions': int(num_solutions * 4),
				   'edit_cost': 'CONSTANT',  # use CONSTANT cost.
				   # the distance between non-symbolic node/edge labels is computed by euclidean distance.
				   'attr_distance': 'euclidean',
				   'ratio_runs_from_initial_solutions': 0.25,
				   # parallel threads. Do not work if mpg_options['parallel'] = False.
				   'threads': multiprocessing.cpu_count(),
				   'init_option': 'EAGER_WITHOUT_SHUFFLED_COPIES'
				   }

	edit_cost_constants = set_edit_cost_consts(ratio,
											node_labeled=len(dataset.node_labels),
											edge_labeled=len(dataset.edge_labels),
											mode='uniform')
#	edit_cost_constants = [item * 0.01 for item in edit_cost_constants]
#	pickle.dump(edit_cost_constants, open(save_dir + "edit_costs" + save_file_suffix + ".pkl", "wb"))

	options = ged_options.copy()
	options['edit_cost_constants'] = edit_cost_constants
	options['node_labels'] = dataset.node_labels
	options['edge_labels'] = dataset.edge_labels
	options['node_attrs'] = dataset.node_attrs
	options['edge_attrs'] = dataset.edge_attrs
	parallel = True # if num_solutions == 1 else False

	"""**5.   Compute GED matrix.**"""
	ged_mat = 'error'
	runtime = 0
	try:
		time0 = time.time()
		ged_vec_init, ged_mat, n_edit_operations = compute_geds(dataset.graphs, options=options, repeats=1, parallel=parallel, verbose=True)
		runtime = time.time() - time0
	except Exception as exp:
		print('An exception occured when running this experiment:')
		LOG_FILENAME = save_dir + 'error.txt'
		logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)
		logging.exception(save_file_suffix)
		print(repr(exp))

	"""**6. Get results.**"""

	with open(save_dir + 'ged_matrix' + save_file_suffix + '.pkl', 'wb') as f:
		pickle.dump(ged_mat, f)
	with open(save_dir + 'runtime' + save_file_suffix + '.pkl', 'wb') as f:
		pickle.dump(runtime, f)

	return ged_mat, runtime


def save_trials_as_group(dataset, ds_name, num_solutions, ratio):
	# Return if the group file exists.
	name_middle = '.' + ds_name + '.num_sols_' + str(num_solutions) + '.ratio_' + "{:.2f}".format(ratio) + '.'
	name_group = save_dir + 'groups/ged_mats' +  name_middle + 'npy'
	if check_group_existence(name_group):
		return

	ged_mats = []
	runtimes = []
	num_trials = 100
	for trial in range(1, num_trials + 1):
		print()
		print('Trial:', trial)
		ged_mat, runtime = xp_compute_ged_matrix(dataset, ds_name, num_solutions, ratio, trial)
		ged_mats.append(ged_mat)
		runtimes.append(runtime)

	# Group trials and Remove single files.
	# @todo: if the program stops between the following lines, then there may be errors.
	name_prefix = 'ged_matrix' + name_middle
	group_trials(save_dir, name_prefix, True, True, False, num_trials=num_trials)
	name_prefix = 'runtime' + name_middle
	group_trials(save_dir, name_prefix, True, True, False, num_trials=num_trials)
	update_group_marker(name_group)


def results_for_a_dataset(ds_name):
	"""**1.   Get dataset.**"""
	dataset = get_dataset(ds_name)

	for ratio in ratio_list:
		print()
		print('Ratio:', ratio)
		for num_solutions in num_solutions_list:
			print()
			print('# of solutions:', num_solutions)
			save_trials_as_group(dataset, ds_name, num_solutions, ratio)


def get_param_lists(ds_name, test=False):
	if test:
		num_solutions_list = [1, 10, 20, 30, 40, 50]
		ratio_list = [10]
		return num_solutions_list, ratio_list

	if ds_name == 'AIDS_symb':
		num_solutions_list = [1, 20, 40, 60, 80, 100]
		ratio_list = [0.1, 0.3, 0.5, 0.7, 0.9, 1, 3, 5, 7, 9]
	else:
		num_solutions_list = [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100] # [1, 20, 40, 60, 80, 100]
		ratio_list = [0.1, 0.3, 0.5, 0.7, 0.9, 1, 3, 5, 7, 9, 10][::-1]

	return num_solutions_list, ratio_list


if __name__ == '__main__':
	if len(sys.argv) > 1:
		ds_name_list = sys.argv[1:]
	else:
		ds_name_list = ['Acyclic', 'Alkane_unlabeled', 'MAO_lite', 'Monoterpenoides', 'MUTAG']
# 		ds_name_list = ['Acyclic'] # 'Alkane_unlabeled']
# 		ds_name_list = ['Acyclic', 'MAO', 'Monoterpenoides', 'MUTAG', 'AIDS_symb']

	save_dir = 'outputs/edit_costs.real_data.num_sols.ratios.IPFP/'
	os.makedirs(save_dir, exist_ok=True)
	os.makedirs(save_dir + 'groups/', exist_ok=True)

	for ds_name in ds_name_list:
		print()
		print('Dataset:', ds_name)
		num_solutions_list, ratio_list = get_param_lists(ds_name, test=False)
		results_for_a_dataset(ds_name)
