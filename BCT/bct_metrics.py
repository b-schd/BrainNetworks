#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 14 11:30:41 2022

Run Brain connectivity methods on networks

@author: bscheid
"""

import bct
import os.path as pth
import glob
import re
from scipy.io import savemat, loadmat
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from multiprocessing import Pool



def calcNodalBCTMets(folderPath, netFuncs, funcNames, ptID, nNets = None):
    
    bands = ['alphatheta', 'beta', 'lowgamma', 'highgamma']
    assert len(funcNames) == len(netFuncs)
    
    # Get network paths, parse filenames
    netPaths = glob.glob(pth.join(folderPath, ptID, '%s*ictal*multiband.mat'%(ptID)));
    m = [re.search("-([pre]*ictal)-block-(\d*)", net).groups() for net in netPaths];
    

    ID, cliptype, sznum, band_nm, data_length = [], [], [], [], []
    metricArrays = [[] for i in range(0,len(funcNames))]

    
    for i_net in range(0, np.min((nNets,len(netPaths)))): #Iterate through networks
        nets = loadmat(netPaths[i_net])
        
        print('loading adjacency matrix from %s'%pth.basename(netPaths[i_net]))
        
        for band in bands:              # Iterate through bands
            adjs = nets.get('adj_'+band)
            
            if len(np.unique(adjs.shape[0:2])) > 1:
                funcDim = 1
                data_length.append(adjs.shape[0])
            else: 
                funcDim = 0
                data_length.append(adjs.shape[2])
                        
            ID.append(ptID)
            cliptype.append(m[i_net][0])
            sznum.append(m[i_net][1])
            band_nm.append(band)
      
            
            for i_f in range(0,len(funcNames)):
                func = netFuncs[i_f]
                met =[netFuncs[i_f](A) for A in adjs]
                metricArrays[i_f].append(met)
                
        df = pd.DataFrame(list(zip(ID, cliptype, sznum, band_nm, data_length, *metricArrays)),
                          columns = ["ID", "type", "sznum", "band", "data_length"]+ funcNames)
           
    return df
    
def getModularity(A, niter=100):
    
    coms = [[] for i in range(0,niter)]
    qs = np.zeros(niter)
    
    for i in range(0,niter):
       (coms[i], qs[i]) = bct.community_louvain(A)
       
    pfinal = coms[np.argsort(qs)[len(qs)//2]]
    # Method takes very long:
    #D = bct.agreement(np.array(coms).T)
    #pfinal = bct.consensus_und(np.divide(D, niter), 0)
    #qstats = np.percentile(qs, [.25, .5, .75])

    
    return pfinal
    
    
  
def loadNetworks(pth, ptID):
    nets = glob.glob(pth.join(folderPath, ptID, '%s*ictal*multiband.mat'%(ptID)))
    
    
    
def _paralell_calcNodalBCTMets(pth, netFuncts, funcNames, ptIDs):
    
    pool = Pool(len(ptIDS)) 
    #BCT_structs = pool.map(partial(calcNodalBCTMets(pth, netFuncs, funcNames), ptIDS))

    
    # bname = ['adj_'+bandname(i) for i in bands]
    # sname = ['syn_'+bandname(i) for i in bands]
    
    # savedict = dict(zip(bname, [A_lists[i][0] for i in range(len(bands))]))
    # savedict.update(dict(zip(sname, [A_lists[i][1] for i in range(len(bands))])))
    # savedict.update({'channels': A_lists[0][2]})
        
    # savemat(outputmat+'-pRef-'+str(pRef).replace('.', '_')+'-multiband.mat', savedict)    
    

if __name__ == '__main__':
    # Load patient networks
    # Define functions to run
    # save network files
    
    
    folderPath = '/Volumes/public/USERS/bscheid/pb17_sync_proj/Data_out/'
    ptIDS = [pth.basename(x) for x in glob.glob(pth.join(folderPath, '[!.]*'))]
    
    netFuncs = [bct.strengths_und, bct.core_periphery_dir, bct.betweenness_wei, getModularity]
    funcNames = ['strength', 'core_periphery', 'betweeness_centrlity', 'modularity']
    
    
    ptID = 'HUP137'
    print(ptID)
    metric_df = calcNodalBCTMets(folderPath, netFuncs, funcNames, ptID, nNets = 2)
    savemat(pth.join(folderPath, ptID,'%s-BCTmetrics.mat'%ptID), {'BCTmetrics': metric_df.to_dict("list")})
    metric_df.to_pickle(pth.join(folderPath, ptID,'%s-BCTmetrics.pkl'%ptID))
    
    
    
    #_paralell_calcNodalBCTMets(pth, netFuncs, funcNames, ptIDS)