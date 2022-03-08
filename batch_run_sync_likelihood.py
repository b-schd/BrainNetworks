#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  7 13:41:26 2022

@author: bscheid
"""

#batch_run_sync_likelihood

from BrainNetworks import construct_sync_likelihood_nets
#from timebudget import timebudget
from multiprocessing import Pool
from functools import partial
import h5py
import sys
import json
import os


def likelihood_wrapper(fpath, chan_ignore, band):
    print(band)
    print(chan_ignore)
    with h5py.File(fpath, 'r') as f:
        print(f.filename)
        A_list = construct_sync_likelihood_nets(f, band=band, chan_ignore=chan_ignore)
        
    # return A_list
    

def run_in_parallel(fpath, bands, chan_ignore):
    pool = Pool(len(bands)) #processes=len(bands))
    N = pool.map(partial(likelihood_wrapper,fpath, chan_ignore), bands)
    # pool.close()
    # pool.join()
    
    return N


def getDataFilePaths(data_config, ptID, path_prefix = None):
    
    evt_list = list(data_config['PATIENTS'][ptID]['Events']['Ictal'].keys())
    fnames = [data_config['PATIENTS'][ptID]['Events']['Ictal'][evt]['FILE'] for evt in evt_list]
    
    if path_prefix:
        fnames = [os.path.join(path_prefix, ptID, f) for f in fnames]
    
    return fnames
    


if __name__ == '__main__':
    
    sysPT = sys.argv[1:] # Input patient ID, otherwise all patients will run


    with open('DATA_config.json') as json_data:
        data_config = json.load(json_data)
        
    
    dir_path = data_config['DIR_PATH']
    bands = [[5,15], [15,30],[30,50], [80,100]]


    # Default is to create networks from all patients
    if sysPT:
        print(sysPT)
        ptList = sysPT
    else:
        print('Creating networks for all patients in DATA_config')
        ptList = list(data_config['PATIENTS'].keys())
        

    for ptID in ptList:
        print(ptID)
        fpaths = getDataFilePaths(data_config, ptID, dir_path)
        chan_ignore= data_config['PATIENTS'][ptID]['IGNORE_ELECTRODES']
        
        # with h5py.File(fpaths[0], 'r') as f:
        #     A_list = construct_sync_likelihood_nets(f, band=bands[0], chan_ignore=chan_ignore)
        
        A_lists = run_in_parallel(fpaths[0], bands, chan_ignore)
        
        


