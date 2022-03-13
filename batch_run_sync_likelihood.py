#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  7 13:41:26 2022

@author: bscheid
"""

#batch_run_sync_likelihood

from BrainNetworks import construct_sync_likelihood_nets
from timebudget import timebudget
from multiprocessing import Pool
from functools import partial
from scipy.io import savemat
import h5py
import sys
import json
import os


def likelihood_wrapper(fpath, chan_ignore, outputmat, band):
    print(band)
    with h5py.File(fpath, 'r') as f:
        print(f.filename)
        A_list, channels = construct_sync_likelihood_nets(f, band=band, chan_ignore=chan_ignore)
    
    savemat(outputmat+'_'+bandname(band)+'.mat',
            {bandname(band): A_list, 'channels': channels})
    return A_list
    
@timebudget
def run_in_parallel(fpath, bands, chan_ignore, outputmat):
    pool = Pool(len(bands)) #processes=len(bands))
    N = pool.map(partial(likelihood_wrapper,fpath, chan_ignore, outputmat), bands)
    # pool.close()
    # pool.join()
    
    return N


def getDataFilePaths(data_config, ptID, path_prefix = None):
    
    evt_list = list(data_config['PATIENTS'][ptID]['Events']['Ictal'].keys())
    fnames = [data_config['PATIENTS'][ptID]['Events']['Ictal'][evt]['FILE'] for evt in evt_list]
    
    if path_prefix:
        fnames = [os.path.join(path_prefix, ptID, f) for f in fnames]
    
    return fnames

def bandname(band):
    if band == [5,15]:
        name = 'adj_alphatheta'
    elif band == [15,30]:
        name = 'adj_beta'
    elif band == [30,50]:
        name = 'adj_lowgamma'
    elif band == [80,100]:
        name = 'adj_highgamma'
    else:
        name = 'adj_%d-%d'%(band[0], band[1])

    return name
    


if __name__ == '__main__':
    
    sysPT = sys.argv[1:] # Input patient ID, otherwise all patients will run


    with open('DATA_config.json') as json_data:
        data_config = json.load(json_data)
        
    
    dir_path = data_config['DIR_PATH']
    out_path = data_config['OUTPUT_PATH']
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
        
        ptOutPath = os.path.join(out_path, ptID) 
        os.makedirs(ptOutPath, exist_ok=True)
        
        matname = fpaths[0].split('/')[-1][:-4].split('-')
        matname.insert(1, 'syncLikelihood')
        
        outputmat = os.path.join(ptOutPath, '_'.join(matname))

       # A_list = likelihood_wrapper(fpaths[0], chan_ignore, outputmat, bands[2])
        A_lists = run_in_parallel(fpaths[0], bands, chan_ignore, outputmat)
        
        


