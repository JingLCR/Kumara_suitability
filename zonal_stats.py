# -*- coding: utf-8 -*-
"""
Created on Thu Jun  4 10:23:58 2020

@author: GuoJ
"""
from __future__ import division
from os.path import join

import numpy as np

#import datetime as dt
from raster import Raster
import pandas as pd
import datetime as dt

#import multiprocessing as mp
#from queue import Empty
#import math
#import time
#import random
from multiprocessing import Pool
#import tqdm


import sys


root_dir = r'D:\projects\682002-0037 PFR 1 Landuse Suitability'
    
data_dir = join(root_dir, r'suitability_maps_nz_smap_oid_test\Kumara')  
out_dir = join(root_dir, r'suitability_maps_nz_smap_oid_test\Kumara')  

res = 0.1  # resolution of raster in km

rst = Raster()

oid_rst = join(root_dir, r'covariate_nz_smap_oid_test\for_suitability_mapping\OID.tif')
ref_rst = oid_rst
ref_array = rst.getRasterArray(ref_rst)
no_data = rst.getNoDataValue(ref_rst)

ref_array= np.where(ref_array==no_data, np.NaN, ref_array)
oid_array = ref_array

suit_rst = join(data_dir,'KM_suitability.tif')
suit_array = rst.getRasterArray(suit_rst)
suit_array= np.where(suit_array==no_data, np.NaN, suit_array)

oid_list = [int(x) for x in np.unique(oid_array[~np.isnan(oid_array)]).tolist()]

len(oid_list)

header = ['OID', 'WS_area', 'S_area', 'MS_area', 'US_area', 'no_data_area', 'total_area', 
          'WS_perc', 'S_perc', 'MS_perc', 'US_perc', 'no_data_perc', 'adj']

s_c_dict = {'WS' : 1, 
            'S'  : 2, 
            'MS' : 3,
            'US' : 4}     

#df = pd.DataFrame(columns=header, dtype=np.float32)
#df = df.astype({'OID': 'int32'})
#
#df.OID = oid_list

#oid_list = oid_list[:10]
    
oid_len = len(oid_list)


def processbyOID2(oid):
    stats_list= []
#    time.sleep(random.random())
#    pbar.update(1)
    stats_list.append(oid)
    # print('Start at {}.'.format(dt.datetime.now()))
    exp = oid_array==oid
    total_area = exp.sum() * res**2    # use km2 as unit
    stats_list.append(total_area)
#    df.loc[df['OID']==oid, 'total_area'] = total_area
#    print(df.loc[df['OID']==oid, 'total_area'])
    exp = np.logical_and(oid_array==oid, suit_array==np.NaN)
    no_data_area = exp.sum() * res**2
    stats_list.append(no_data_area)
    stats_list.append(round(no_data_area / total_area, 4)) # no data percentage
#    df.loc[df['OID']==oid, 'no_data_area'] = no_data_area
#    df.loc[df['OID']==oid, 'no_data_perc'] = round(no_data_area / total_area, 4)

    # print('Total and None done at {}.'.format(dt.datetime.now()))
    # sum_perc = 0
    for s_c in s_c_dict:      # four catagories of suitability
        exp = np.logical_and(oid_array==oid, suit_array==s_c_dict[s_c])
        s_area = exp.sum() * res**2
        stats_list.append(s_area)
#        df.loc[df['OID']==oid, '{}_area'.format(s_c)] = s_area

        s_perc = round(s_area / total_area, 4)
        stats_list.append(s_perc)
        
#        df.loc[df['OID']==oid, '{}_perc'.format(s_c)] = s_perc

        # if s_c != 'US':
        #     df.loc[df['OID']==oid, '{}_perc'.format(s_c)] = s_perc
        #     sum_perc += s_perc
        # else:
        #     if sum_perc + s_perc == 1:
        #         df.loc[df['OID']==oid, '{}_perc'.format(s_c)] = s_perc
        #     else:
        #         df.loc[df['OID']==oid, '{}_perc'.format(s_c)] = 1 - sum_perc
        #         print('s_perc: {}, 1-sum_perc: {}'.format(s_perc, 1 - sum_perc))
    
    # print('Suit cls done at {}.'.format(dt.datetime.now()))

#    total_perc = df[df['OID']==oid][['WS_perc', 'S_perc', 'MS_perc', 'US_perc', 'no_data_perc']].sum(axis=1).values[0]
#    if total_perc != 1:
#        df.loc[df['OID']==oid, 'US_perc'] = 1 - df[df['OID']==oid][['WS_perc', 'S_perc', 'MS_perc', 'no_data_perc']].sum(axis=1).values[0]
#        df.loc[df['OID']==oid, 'adj'] = 1
#    else:
#        df.loc[df['OID']==oid, 'adj'] = 0
    total_perc = stats_list[-1] + stats_list[-3] + stats_list[-5] + stats_list[-7]
    stats_list.append(1) #total percentage
    if total_perc != 1:
        stats_list[-1] = 1 - (stats_list[-3] + stats_list[-5] + stats_list[-7])
        stats_list.append(1) # adj indicator
    else:
        stats_list.append(0) # adj indicator
    

    return stats_list

if __name__ == '__main__':
    
    print('Start at {}.'.format(dt.datetime.now()))
    s_list=[]
    #pbar = tqdm.tqdm(total=oid_len)
    #
    pool = Pool(8)
    #pool.map(processbyOID2,oid_list)
    #
    #pool.close()
    #pool.join()
    #pbar.close()
    
#    for oid in oid_list:
#        processbyOID2(oid)
    
    for i, _ in enumerate(pool.imap_unordered(processbyOID2, oid_list), 1):
        sys.stderr.write('\rdone {0:%}'.format(i/oid_len))
        s_list.append(_)
    
#    s_list = pool.imap(processbyOID2, oid_list)
    pool.close()
    
#    print(s_list)
    

    df = pd.DataFrame(s_list, columns=['OID', 
                                                'total_area', 
                                                'no_data_area',
                                                'no_data_perc', 
                                                'WS_area', 
                                                'WS_perc', 
                                                'S_area', 
                                                'S_perc', 
                                                'MS_area',
                                                'MS_perc',  
                                                'US_area',  
                                                'US_perc', 
                                                'total_perc', 
                                                'adj'])
    

    
    df.to_csv(join(out_dir, 'smap_suit_zonal_stats_100m.csv'))
    
    print('End at {}.'.format(dt.datetime.now()))
