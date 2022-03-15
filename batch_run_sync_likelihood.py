#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  7 13:41:26 2022

@author: bscheid
"""

#batch_run_sync_likelihood

from BrainNetworks import construct_sync_likelihood_nets, synchronizability
from timebudget import timebudget
from multiprocessing import Pool
from functools import partial
from scipy.io import savemat, loadmat
import numpy as np
import h5py
import sys
import json
import os


def likelihood_wrapper(fpath, chan_ignore, outputmat, pRef, band):
    print(band)
    
    try:
        f = loadmat(fpath)        
    except NotImplementedError:
        f = h5py.File(fpath)
        print(f.filename)            
    except:
        print('Error reading f at %s'%fpath)
        ValueError('could not read at all...')
    
    A_list, channels = construct_sync_likelihood_nets(f, band=band, pRef=pRef, chan_ignore=chan_ignore)
    syn = [synchronizability(A_list[i]) for i in range(len(A_list))]
    
    savemat(outputmat+'_pRef_'+str(pRef).replace('.', '_')+'_adj_'+bandname(band)+'.mat',
            {'adj_'+bandname(band): A_list, 'channels': channels,
             'syn_'+bandname(band): np.transpose(syn)})
        
    return A_list
    
@timebudget
def run_in_parallel(fpath, bands, chan_ignore, outputmat, pRef):
    pool = Pool(len(bands)) #processes=len(bands))
    N = pool.map(partial(likelihood_wrapper,fpath, chan_ignore, outputmat, pRef), bands)
    # pool.close()
    # pool.join()
    
    return N

def getDataFilePaths(data_config, ptID, path_prefix = None):
    evt_list = list(data_config['PATIENTS'][ptID]['Events']['Ictal'].keys())
    fnames = [data_config['PATIENTS'][ptID]['Events']['Ictal'][evt]['FILE'] for evt in evt_list]
    if path_prefix:
        fnames_ictal = [os.path.join(path_prefix, ptID.split('_')[0], f) for f in fnames]   
    fnames_preictal = [s.replace('ictal', 'preictal') for s in fnames_ictal]
    return (fnames_ictal, fnames_preictal)

def bandname(band):
    if band == [5,15]:
        name = 'alphatheta'
    elif band == [15,30]:
        name = 'beta'
    elif band == [30,50]:
        name = 'lowgamma'
    elif band == [80,100]:
        name = 'highgamma'
    else:
        name = '%d-%d'%(band[0], band[1])

    return name
    


if __name__ == '__main__':
    
    sysPT = sys.argv[1:] # Input patient ID, otherwise all patients will run


    with open('DATA_config.json') as json_data:
        data_config = json.load(json_data)
        
    
    dir_path = data_config['DIR_PATH']
    out_path = data_config['OUTPUT_PATH']
    bands = [[5,15],[15,30],[30,50],[80,100]]
    pRef = 0.5; 


    # Default is to create networks from all patients
    if sysPT:
        print(sysPT)
        ptList = sysPT
    else:
        print('Creating networks for all patients in DATA_config')
        ptList = list(data_config['PATIENTS'].keys())
        

    for ptID in ptList:
        print(ptID)
        fpaths_ictal, fpaths_preictal = getDataFilePaths(data_config, ptID, dir_path)
        chan_ignore= data_config['PATIENTS'][ptID]['IGNORE_ELECTRODES']
        
        ptOutPath = os.path.join(out_path, ptID.split('_')[0]) 
        os.makedirs(ptOutPath, exist_ok=True)
        
        # ICTAL
        matname_ictal = fpaths_ictal[0].split('/')[-1][:-4].split('-')
        matname_ictal.insert(1, 'syncLikelihood')
        outputmat_ictal = os.path.join(ptOutPath, '_'.join(matname_ictal))
        A_lists = run_in_parallel(fpaths_ictal[0], bands, chan_ignore, outputmat_ictal, pRef)
        
        # PREICTAL
        matname_preictal = fpaths_preictal[0].split('/')[-1][:-4].split('-')
        matname_preictal.insert(1, 'syncLikelihood')
        outputmat_preictal = os.path.join(ptOutPath, '_'.join(matname_preictal))
        A_lists = run_in_parallel(fpaths_preictal[0], bands, chan_ignore, outputmat_preictal, pRef)
        
        
        #A_list = likelihood_wrapper(fpaths_ictal[0], chan_ignore, outputmat_ictal, pRef, bands[2])

        
        
        


