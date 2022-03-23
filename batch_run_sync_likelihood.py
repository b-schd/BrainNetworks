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
import argparse
import h5py
import sys
import json
import os


def likelihood_wrapper(fpath, chan_ignore, chan_keep, outputmat, pRef, band):
    print(band)
    
    try:
        f = loadmat(fpath)        
    except NotImplementedError:
        f = h5py.File(fpath)
        print(f.filename)            
    except:
        print('Error reading f at %s'%fpath)
        ValueError('could not read at all...')
    
    A_list, channels = construct_sync_likelihood_nets(f, band=band, pRef=pRef,
                                                      chan_ignore=chan_ignore,
                                                      chan_keep = chan_keep)
    syn = [synchronizability(A_list[i]) for i in range(len(A_list))]
    
    return A_list, syn, channels
    
@timebudget
def run_in_parallel(fpath, bands, chan_ignore, chan_keep, outputmat, pRef):
    pool = Pool(len(bands)) #processes=len(bands))
    A_lists = pool.map(partial(likelihood_wrapper,fpath, chan_ignore, chan_keep, outputmat, pRef), bands)
    # pool.close()
    #pool.join()
    
    bname = ['adj_'+bandname(i) for i in bands]
    sname = ['syn_'+bandname(i) for i in bands]
    
    savedict = dict(zip(bname, [A_lists[i][0] for i in range(len(bands))]))
    savedict.update(dict(zip(sname, [A_lists[i][1] for i in range(len(bands))])))
    savedict.update({'channels': A_lists[0][2]})
        
    savemat(outputmat+'-pRef-'+str(pRef).replace('.', '_')+'-multiband.mat', savedict)
    
    
    return A_lists

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
        name = '%d_%d'%(band[0], band[1])

    return name
    


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument('sysPT', nargs='?', default=None, help='Patient ID (e.g. HUP108)')
    parser.add_argument('--pref', type=float, default=0.5)
    parser.add_argument('--config', default='DATA_config.json', help='path to config file')
    parser.add_argument('--fpath', default= None)
    args = parser.parse_args()
    

    with open(args.config) as json_data:
        data_config = json.load(json_data)
         
    dir_path = data_config['DIR_PATH']
    out_path = data_config['OUTPUT_PATH']
    bands = [[5,15],[15,30],[30,50],[80,100]]
    pRef = args.pref
    
    print('Using pRef= %0.2f'%(pRef))

    # Default is to create networks from all patients
    if args.sysPT:
        ptList = [args.sysPT]
    else:
        print('Creating networks for all patients in DATA_config')
        ptList = list(data_config['PATIENTS'].keys())
        

    for ptID in ptList:
        print(ptID)
        fpaths_ictal, fpaths_preictal = getDataFilePaths(data_config, ptID, dir_path)
        
        if ('CLEAN_GRID_NAMES' in (data_config['PATIENTS'][ptID]).keys()):
            chan_ignore = None
            chan_keep = data_config['PATIENTS'][ptID]['CLEAN_GRID_NAMES']
        else:
            chan_ignore = data_config['PATIENTS'][ptID]['IGNORE_ELECTRODES']
            chan_keep = None
            
        
        ptOutPath = os.path.join(out_path, ptID.split('_')[0]) 
        os.makedirs(ptOutPath, exist_ok=True)
        
        if args.fpath:
            matname= args.fpath.split('/')[-1][:-4].split('-')
            matname.insert(1, 'syncLikelihood')
            outputmat = os.path.join(ptOutPath, '-'.join(matname))
            A_lists = run_in_parallel(args.fpath, bands, chan_ignore, chan_keep, outputmat, pRef)
            #A_list = likelihood_wrapper(args.fpath, chan_ignore, chan_keep, outputmat, pRef, bands[2])

            print(args.fpath)
            break
            
        
        # ICTAL
        for i_pth in range(len(fpaths_ictal)):
            matname_ictal = fpaths_ictal[i_pth].split('/')[-1][:-4].split('-')
            matname_ictal.insert(1, 'syncLikelihood')
            outputmat_ictal = os.path.join(ptOutPath, '-'.join(matname_ictal))
            #A_lists = run_in_parallel(fpaths_ictal[i_pth], bands, chan_ignore, chan_keep, outputmat_ictal, pRef)
        
        # PREICTAL
        for i_pth in range(len(fpaths_preictal)):
            matname_preictal = fpaths_preictal[i_pth].split('/')[-1][:-4].split('-')
            matname_preictal.insert(1, 'syncLikelihood')
            outputmat_preictal = os.path.join(ptOutPath, '-'.join(matname_preictal))
            A_lists = run_in_parallel(fpaths_preictal[i_pth], bands, chan_ignore, chan_keep, outputmat_preictal, pRef)
        
        
        #A_list = likelihood_wrapper(fpaths_ictal[0], chan_ignore, chan_keep, outputmat_ictal, pRef, bands[2])

        
        
        


