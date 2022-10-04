# -*- coding: utf-8 -*-
"""
Created on Mon Mar 26 13:40:26 2018

@author: 
    
This script is for SLMACC project. It is the third step of land suitability mapping.
It creates land suitability maps for each crop of each contributing covariate layer, 
as well as an overall suitability map for each crop.    

"""

# -*- coding: utf-8 -*-
"""
Created on Wed Jan 17 10:50:10 2018
Revised on 29 June 2018 (v2)
Land suitability model
@author: Jing Guo
"""

import os
from os.path import join

import numpy as np
import sys
from os import walk
import CSVOperation
import datetime as dt

from config import ConfigParameters
from raster import Raster
from sqlite_conn import Sqlite_connection

# =============================================================================
# def DataTypeConversion(x):
#     return {
#             'Real': gdal.GDT_Float32,
#             'Integer': gdal.GDT_Int32,
#         }.get(x, gdal.GDT_Unknown)
#     
# 
# def DataTypeConversion_GDAL2NP(x):
#     return {
#             5: np.int,
#             6: np.float,
#         }.get(x, np.float)
# =============================================================================
def WeightedSum_limit(crop_id, array_list, id_list, conn):
    
    summed_array = np.zeros(array_list[0].shape)  
    i=0  
    for cova_id, suit_array in zip(id_list, array_list):
        print(i)
        with conn as cur:
            weight = cur.execute("select weight from covariate_weight where crop_id=? and covariate_id=?", (crop_id, cova_id,)).fetchone()['weight']
            
        suit_array = np.where(suit_array == 1, 30, suit_array)
        suit_array = np.where(suit_array == 2, 20, suit_array)
        suit_array = np.where(suit_array == 3, 10, suit_array)
        suit_array = np.where(suit_array == 4, -1000, suit_array)
        
        suit_array = np.where(suit_array == 30, 3, suit_array)
        suit_array = np.where(suit_array == 20, 2, suit_array)
        suit_array = np.where(suit_array == 10, 1, suit_array)
        
        summed_array = summed_array + suit_array * weight 
        i+=1
         
    summed_array = np.around(summed_array, decimals=2)    
    summed_array = np.where(summed_array < 0, 0, summed_array)
#    summed_array = np.rint(summed_array)

    return summed_array        


def WeightedSum(crop_id, array_list, id_list, conn):
    
    summed_array = np.zeros(array_list[0].shape)  
    i=0  
    for cova_id, suit_array in zip(id_list, array_list):
        print(i)
        with conn as cur:
            weight = cur.execute("select weight from covariate_weight where crop_id=? and covariate_id=?", (crop_id, cova_id,)).fetchone()['weight']
            
        suit_array = np.where(suit_array == 1, 30, suit_array)
        suit_array = np.where(suit_array == 2, 20, suit_array)
        suit_array = np.where(suit_array == 3, 10, suit_array)
        suit_array = np.where(suit_array == 4, 0, suit_array)
        
        suit_array = np.where(suit_array == 30, 3, suit_array)
        suit_array = np.where(suit_array == 20, 2, suit_array)
        suit_array = np.where(suit_array == 10, 1, suit_array)
        
        summed_array = summed_array + suit_array * weight 
        i+=1
         
    summed_array = np.around(summed_array, decimals=2)    
    summed_array = np.where(summed_array < 0, 0, summed_array)
#    summed_array = np.rint(summed_array)

    return summed_array        
            
            
def ExtractMaxValueOfStack(array_list):
    
    suit_array_stack = np.dstack(array_list)
    # Get the index values for the minimum and maximum values
    maxIndex = np.argmax(suit_array_stack, axis=2)
#    minIndex = np.argmin(suit_array_stack, axis=2)
    
    # Create column and row position arrays
    nRow, nCol = np.shape(array_list[0])
    col, row = np.meshgrid(range(nCol), range(nRow))
    
    # Index out the maximum and minimum values from the stacked array based on row 
    # and column position and the maximum value
    maxValue_array = suit_array_stack[row, col, maxIndex]
#    minValue = suit_array_stack[row, col, minIndex]
    
    return maxValue_array

def ExtractMaxValueIndexBinaryOfStack(array_list, name_list, max_value):
    
    def getNameGroup(binary_string, name_list):
        
        binary_string = binary_string[2:] # Remove the first two charactors '0b'
        
        name_group = []
        
        for i in range(0, len(binary_string)):
            if binary_string[i] == '1':
                name_group.append(name_list[i])
        
        return name_group

    
    max_index_binary_array = '0b'
    max_count_array = np.zeros(array_list[0].shape)
    
    for array in array_list:
        max_index_array = np.where(array == max_value, '1', '0')
        max_index_binary_array = np.core.defchararray.add(max_index_binary_array, max_index_array)
        
        max_array = np.where(array == max_value, 1, 0)
        max_count_array = max_count_array + max_array
        
        
    max_index_int_array = np.zeros(max_index_binary_array.shape)
    for i in range(0, len(max_index_binary_array)):
        for j in range(0, len(max_index_binary_array[i])):
            max_index_int_array[i][j] = int(max_index_binary_array[i][j], 2)
    
    
    unique_binary_list = list(np.unique(max_index_binary_array))
    
    max_value_legend_list = []
    
    for binary in unique_binary_list:
        
        key = int(binary, 2)
        group_name = getNameGroup(binary, name_list)
        max_value_legend_list.append([key, len(group_name), '&'.join(group_name)])
        
    return max_index_int_array, max_count_array, max_value_legend_list


def homogenize_nodata_area(array_list, NoData):
    '''
    This function is used to create a mask array, 
    and its' Nodata grids match all the Nodata grids in 
    each array in the array list. 
    '''
    for i in range(0, len(array_list)):
        if i == 1:
            exp = np.logical_and(array_list[i]!= NoData, array_list[i-1]!= NoData,)
        elif i > 1:
            exp = np.logical_and(exp, array_list[i]!= NoData)
    
    ref_array = np.where(exp, array_list[0], NoData)
    return ref_array


def strip_end(text, suffix):
    if not text.endswith(suffix):
        return text
    return text[:len(text)-len(suffix)]

def strip_start(text, suffix):
    if not text.startswith(suffix):
        return text
    return text[len(suffix):]


class LandSuitability(object):
    
    def __init__(self):
        self.no_data = ''
    
    def __reclassify_contianual__(self, covariate_array, rulesets):
        
        suit_array = np.zeros(covariate_array.shape)  # an empty array for suitability array (fill with value afterwards)
        direction = ''
        
        for row in rulesets:
            suit_level = row['suitability_level']
            low1 = row['low_value']
            high1 = row['high_value']
            low2 = row['low_value_2']
            high2 = row['high_value_2']
            
            # Here we deal with the suitability level one, from which we derive the direction of covariate response curve
            if suit_level == 1:
                # This is bell shaped curve situation 
                # (only under this circumstance low2 or high2 of the rest of suitability level may exist)
                if low1 is not None and high1 is not None: 
                    direction = 'two'
                    suit_array = np.where(np.logical_and(covariate_array>=low1, covariate_array<high1), suit_level, suit_array)
                                  
                # This is one direction descending situation
                elif low1 is not None and high1 is None:     
                    direction = 'descd'
                    suit_array = np.where(covariate_array>=low1, suit_level, suit_array)
                    
                # This is one direction ascending situation
                elif low1 is None and high1 is not None:     
                    direction = 'ascd'
                    suit_array = np.where(covariate_array<=high1, suit_level, suit_array)
                    
                # This is low1 and high1 are both None, which shouldn't exist    
                else:
                    print('Warning! Unexpected "None" value exist in both "low_value" and "high_value" of' 
                          'suitability level 1 of crop {}, covariate {}. Please check the database and' 
                          'set the correct values.'.format(row['crop_id'], row['covariate_id']))
            
            # From here we dealing with the rest of suitability levels
            else:
                # If it is one direction (ascending or descending), then we don't have to care about the low2 and high2
                if direction == 'descd':
                    if low1 is not None and high1 is not None:
                        suit_array = np.where(np.logical_and(covariate_array>=low1, covariate_array<high1), suit_level, suit_array)
                    elif low1 is None and high1 is not None:
                        suit_array = np.where(covariate_array<high1, suit_level, suit_array)

                elif direction == 'ascd':
                    if low1 is not None and high1 is not None:
                        suit_array = np.where(np.logical_and(covariate_array>low1, covariate_array<=high1), suit_level, suit_array)
                    elif low1 is not None and high1 is None:
                        suit_array = np.where(covariate_array>low1, suit_level, suit_array)
                
                # If it is two direction then we deal with the most complex situation 
                else:
                    if low1 is not None and high1 is not None:
                        if low2 is not None and high2 is not None:
                            suit_array = np.where(np.logical_or(np.logical_and(covariate_array>=low1, covariate_array<high1), 
                                                                np.logical_and(covariate_array>=low2, covariate_array<high2)), 
                                                  suit_level, suit_array)
                        elif low2 is None and high2 is not None:
                            suit_array = np.where(np.logical_or(np.logical_and(covariate_array>=low1, covariate_array<high1), 
                                                                covariate_array<high2), 
                                                  suit_level, suit_array)
                        elif low2 is not None and high2 is None:
                            suit_array = np.where(np.logical_or(np.logical_and(covariate_array>=low1, covariate_array<high1), 
                                                                covariate_array>=low2), 
                                                  suit_level, suit_array)
                        else:
                            suit_array = np.where(np.logical_and(covariate_array>=low1, covariate_array<high1), suit_level, suit_array)
                        
                    elif low1 is None and high1 is not None:
                        if low2 is not None and high2 is not None:
                            suit_array = np.where(np.logical_or(covariate_array<high1, 
                                                                np.logical_and(covariate_array>=low2, covariate_array<high2)), 
                                                  suit_level, suit_array)
                        elif low2 is not None and high2 is None:
                            suit_array = np.where(np.logical_or(covariate_array<high1, 
                                                                covariate_array>=low2), 
                                                  suit_level, suit_array)
                        #This situation shouln't exist, because bath low1 and low2 are none means tow parts are in the same direction
                        elif low2 is None and high2 is not None:
                            print('Warning! Unexpected value exist in either "low_value_1" or "low_value_2" of suitability'
                                  'level {} of crop {}, covariate {}. Please check the database and set the correct'
                                  'values.'.format(row['suitability_level'], row['crop_id'], row['covariate_id']))
                        else:
                            suit_array = np.where(covariate_array<high1, suit_level, suit_array)
                    
                    elif low1 is not None and high1 is None:
                        if low2 is not None and high2 is not None:
                            suit_array = np.where(np.logical_or(covariate_array>=low1, 
                                                                np.logical_and(covariate_array>=low2, covariate_array<high2)), 
                                                  suit_level, suit_array)
                        elif low2 is None and high2 is not None:
                            suit_array = np.where(np.logical_or(covariate_array>=low1, 
                                                                covariate_array<high2), 
                                                  suit_level, suit_array)
                        #This situation shouln't exist, because bath low1 and low2 are none means tow parts are in the same direction
                        elif low2 is not None and high2 is None:
                            print('Warning! Unexpected value exist in either "high_value_1" or "high_value_2" of suitability'
                                  'level {} of crop {}, covariate {}. Please check the database and set the correct'
                                  'values.'.format(row['suitability_level'], row['crop_id'], row['covariate_id']))
                        else:
                            suit_array = np.where(covariate_array>low1, suit_level, suit_array)
                    
                    # When both low1 and high1 are None, low2 and high2 must be None, otherwise we should put the low2 and high2 to low1 and high1
                    else:
                        if low2 is not None or high2 is not None:
                            print('Warning! Unexpected value exist in either "low_value_2" or "high_value_2" of suitability'
                                  'level {} of crop {}, covariate {}. Please check the database and set the correct'
                                  'values.'.format(row['suitability_level'], row['crop_id'], row['covariate_id']))
                            
        return suit_array
    
    def __reclassify_catorgorical__(self, covariate_array, rulesets):            
                
        suit_array = np.zeros(covariate_array.shape)  # an empty array for suitability array (fill with value afterwards)
        
        all_cat_values_not_level4 = []
        for row in rulesets:
            suit_level = row['suitability_level']
            
            if row['cat_value'] is not None:
                cat_values = [int(x) for x in row['cat_value'].split(',')]
                suit_array = np.where(np.isin(covariate_array, cat_values), suit_level, suit_array)
                all_cat_values_not_level4 = all_cat_values_not_level4 + cat_values
            
            # If the catorgorical value is None at certian suitability level, then we check if it is at levle 4. 
            # If so then we set the rest of class values to level 4, otherwise don't create that level. 
            else:
                if suit_level == 4:
                    # Set all cells, where their class value is not in the all_cat_values_not_level4 list, to level 4 
                    suit_array = np.where(np.isin(covariate_array, all_cat_values_not_level4, invert=True), suit_level, suit_array)
        
        return suit_array
    
    def mapping(self, crop_id, crop, covariate_rasters, conn, covariate_root_dir, suit_root_dir):
        
        raster = Raster()
        self.no_data =raster.getNoDataValue(covariate_rasters[-1])
        ref_rst = covariate_rasters[-1]
        covariate_id_list = []
        suit_array_stack = []
        
# =============================================================================
#         filepath = strip_end(ref_rst, ref_rst.split('\\')[-1])
#         out_dir = join(suit_root_dir, strip_start(filepath, covariate_root_dir)[1:]) # the [1:] is for removing the first and the last '\' of string
# =============================================================================
        out_dir = join(suit_root_dir, crop)
        
        if not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok = True)
         
        for rst in covariate_rasters:
            
            filename = rst.split('\\')[-1].split('.')[0]
            
            if len(filename.split('_')) == 1:
                covariate_id = filename
                covariate_id_list.append(covariate_id)
                out_raster = join(out_dir, 'suitability_{}_{}.tif'.format(crop_id, covariate_id))
            else:
                covariate_id = filename.split('_')[1]
                covariate_id_list.append(covariate_id)
                time_span = '{}_{}'.format(filename.split('_')[-2], filename.split('_')[-1])
                out_raster = join(out_dir, 'suitability_{}_{}_{}.tif'.format(crop_id, covariate_id, time_span))
            
            with conn as cur:
                rows = cur.execute("select * from suitability_rule where crop_id=? and covariate_id=? order by suitability_level", (crop_id,covariate_id,)).fetchall()
                is_continual = cur.execute("select * from Covariate where id=?", (covariate_id,)).fetchone()['iscontinual']
            
            # If the query returns none then move to the next covariate
            if rows:
                covariate_array = raster.getRasterArray(rst)  # array of the covariate
                
                if is_continual == 1:
                    suit_array = self.__reclassify_contianual__(covariate_array, rows)
                else:
                    suit_array = self.__reclassify_catorgorical__(covariate_array, rows)
                
                suit_array[np.where(covariate_array == self.no_data)] = self.no_data
                
                raster.array2Raster(suit_array, ref_rst, out_raster)
                
                suit_array_stack.append(suit_array)
            else:
                print('Warning! Suitability ruleset for {}, {} not found! Please check the database.'.format(crop_id, covariate_id))
        
        # here is to calculate the overall suitability
        if len(suit_array_stack) > 0:
            crop_suit_array = ExtractMaxValueOfStack(suit_array_stack)
            ref_array = homogenize_nodata_area(suit_array_stack, self.no_data)
            crop_suit_array[np.where(ref_array == self.no_data)] = self.no_data
            crop_suit_raster = join(out_dir, '{}_suitability.tif'.format(crop_id))
            raster.array2Raster(crop_suit_array, ref_rst, crop_suit_raster)
            
            print('create dominant worst covariate raster at {}...'.format(dt.datetime.now()))
            worst_dominant_array, worst_count_array, worst_dominant_legend_list = ExtractMaxValueIndexBinaryOfStack(suit_array_stack, covariate_id_list, 4)
            
            worst_dominant_array[np.where(ref_array == self.no_data)] = self.no_data
            worst_dominant_raster_file = join(out_dir, '{}_worst_dominant.tif'.format(crop_id))
            raster.array2Raster(worst_dominant_array, ref_rst, worst_dominant_raster_file)
            
            worst_count_array[np.where(ref_array == self.no_data)] = self.no_data
            worst_count_raster_file = join(out_dir, '{}_worst_count.tif'.format(crop_id))
            raster.array2Raster(worst_count_array, ref_rst, worst_count_raster_file)
            
            worst_dominant_legend_csv = join(out_dir, '{}_worst_dominant_legend.csv'.format(crop_id))
            csvw = CSVOperation.CSVWriting()
            headers = ['raster value', 'number of restriction', 'covariates']
            csvw.WriteLines(worst_dominant_legend_csv, headers, worst_dominant_legend_list)
        else:
            print('Warning! No suitability map for {} was created!'.format(crop_id))
    
     
    def mappingNIWArule(self, crop_id, covariate_rasters, conn, covariate_root_dir, suit_root_dir):
        
        raster = Raster()
        self.no_data =raster.getNoDataValue(covariate_rasters[-1])
        ref_rst = covariate_rasters[-1]
        covariate_id_list = []
        suit_array_stack = []
        suit_raster_list = []
        overall_suit_array = np.zeros(raster.getRasterArray(ref_rst).shape)
        
        filepath = strip_end(ref_rst, ref_rst.split('\\')[-1])
        out_dir = join(suit_root_dir, strip_start(filepath, covariate_root_dir)[1:]) # the [1:] is for removing the first and the last '\' of string
        
        if not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok = True)
         
        
        for rst in covariate_rasters:
            
            filename = rst.split('\\')[-1].split('.')[0]
            
            if len(filename.split('_')) == 1:
                covariate_id = filename
#                covariate_id_list.append(covariate_id)
                out_raster = join(out_dir, 'suitability_{}_{}.tif'.format(crop_id, covariate_id))
            else:

                covariate_id = filename.split('_')[1]
#                covariate_id_list.append(covariate_id)
                time_span = '{}_{}'.format(filename.split('_')[-2], filename.split('_')[-1])
                out_raster = join(out_dir, 'suitability_{}_{}_{}.tif'.format(crop_id, covariate_id, time_span))
            
            suit_raster_list.append(out_raster)
                
            with conn as cur:
                rows = cur.execute("select * from suitability_rule where crop_id=? and covariate_id=? order by suitability_level", (crop_id,covariate_id,)).fetchall()
                is_continual = cur.execute("select * from Covariate where id=?", (covariate_id,)).fetchone()['iscontinual']
            
            # If the query returns none then move to the next covariate
            if rows:
                covariate_array = raster.getRasterArray(rst)  # array of the covariate
                
                if is_continual == 1:
                    suit_array = self.__reclassify_contianual__(covariate_array, rows)
                else:
                    suit_array = self.__reclassify_catorgorical__(covariate_array, rows)
                
                suit_array[np.where(covariate_array == self.no_data)] = self.no_data
                
                raster.array2Raster(suit_array, ref_rst, out_raster)
                
#                suit_array_stack.append(suit_array)
            else:
                print('Warning! Suitability ruleset for {}, {} not found! Please check the database.'.format(crop_id, covariate_id))
        
        
        if crop_id == 'HM':
            
            HT_array_dict = dict.fromkeys(['s','u','a','w'])
            LM_array_dict = dict.fromkeys(['s','u','a','w'])
            LR_array_dict = dict.fromkeys(['s','u','a','w'])
            
            for rst in suit_raster_list:
                cova_indicator = rst.split('\\')[-1].split('_')[2][:2]
                season_indicator = rst.split('\\')[-1].split('_')[2][2]
                
                if cova_indicator == 'HT':
                    if season_indicator == 'S':
                        HT_array_dict['s'] = raster.getRasterArray(rst)
                    elif season_indicator == 'U':
                        HT_array_dict['u'] = raster.getRasterArray(rst)
                    elif season_indicator == 'A':
                        HT_array_dict['a'] = raster.getRasterArray(rst)
                    elif season_indicator == 'W':
                        HT_array_dict['w'] = raster.getRasterArray(rst)
                elif cova_indicator == 'LM':
                    if season_indicator == 'S':
                        LM_array_dict['s'] = raster.getRasterArray(rst)
                    elif season_indicator == 'U':
                        LM_array_dict['u'] = raster.getRasterArray(rst)
                    elif season_indicator == 'A':
                        LM_array_dict['a'] = raster.getRasterArray(rst)
                    elif season_indicator == 'W':
                        LM_array_dict['w'] = raster.getRasterArray(rst)
                elif cova_indicator == 'LR':
                    if season_indicator == 'S':
                        LR_array_dict['s'] = raster.getRasterArray(rst)
                    elif season_indicator == 'U':
                        LR_array_dict['u'] = raster.getRasterArray(rst)
                    elif season_indicator == 'A':
                        LR_array_dict['a'] = raster.getRasterArray(rst)
                    elif season_indicator == 'W':
                        LR_array_dict['w'] = raster.getRasterArray(rst)
            
                else:
                    suit_array = raster.getRasterArray(rst)
                    suit_array_stack.append(suit_array)
                    suit_array = np.where(suit_array==1, 20, np.where(suit_array==2,10,0))
                    suit_array = np.where(suit_array==20, 2, np.where(suit_array==10,1,0))
                    overall_suit_array = overall_suit_array + suit_array
                    covariate_id_list.append(rst.split('\\')[-1].split('_')[2].split('.')[0])
            
            ht_suit_array = np.where(np.logical_and(np.logical_and(np.logical_and(HT_array_dict['s']==1, 
                                                                                  HT_array_dict['u']==1), 
                                                                   HT_array_dict['a']==1), 
                                                    HT_array_dict['w']==1), 2, 
                                     np.where(np.logical_and(np.logical_and(np.logical_and(np.logical_or(HT_array_dict['s']==2,HT_array_dict['s']==1),
                                                                                           np.logical_or(HT_array_dict['u']==2,HT_array_dict['u']==1)), 
                                                                            np.logical_or(HT_array_dict['a']==2,HT_array_dict['a']==1)), 
                                                             np.logical_or(HT_array_dict['w']==2,HT_array_dict['w']==1)), 1, 
                                     0))
            
            ht_suit_array[np.where(HT_array_dict['s'] == self.no_data)] = self.no_data
            raster.array2Raster(ht_suit_array, ref_rst, join(out_dir, 'suitability_{}_HT.tif'.format(crop_id)))
            suit_array_stack.append(ht_suit_array)
            overall_suit_array = overall_suit_array + ht_suit_array
            covariate_id_list.append('HT')
                    
            lm_suit_array = np.where(np.logical_and(np.logical_and(np.logical_and(LM_array_dict['s']==1, 
                                                                                  LM_array_dict['u']==1), 
                                                                   LM_array_dict['a']==1), 
                                                    LM_array_dict['w']==1), 2, 
                                     np.where(np.logical_and(np.logical_and(np.logical_and(np.logical_or(LM_array_dict['s']==2,LM_array_dict['s']==1), 
                                                                                           np.logical_or(LM_array_dict['u']==2,LM_array_dict['u']==1)), 
                                                                            LM_array_dict['a']==1), 
                                                             LM_array_dict['w']==1), 1, 
                                     0))
            
            lm_suit_array[np.where(LM_array_dict['s'] == self.no_data)] = self.no_data
            raster.array2Raster(lm_suit_array, ref_rst, join(out_dir, 'suitability_{}_LM.tif'.format(crop_id)))
            suit_array_stack.append(lm_suit_array)
            overall_suit_array = overall_suit_array + lm_suit_array
            covariate_id_list.append('LM')
                    
# =============================================================================
#             lr_suit_array = np.where(np.logical_and(np.logical_and(np.logical_and(LR_array_dict['s']==1, 
#                                                                                   LR_array_dict['u']==1), 
#                                                                    LR_array_dict['a']==1), 
#                                                     LR_array_dict['w']==1), 1, 
#                                      np.where(np.logical_and(np.logical_and(np.logical_and(LR_array_dict['s']==2, 
#                                                                                            LR_array_dict['u']==2), 
#                                                                             LR_array_dict['a']==2), 
#                                                              LR_array_dict['w']==2), 2, 
#                                      4))
#             
#             lr_suit_array[np.where(covariate_array == self.no_data)] = self.no_data
#             raster.array2Raster(lr_suit_array, ref_rst, join(out_dir, 'suitability_{}_LR.tif'.format(crop_id)))
#             suit_array_stack.append(lr_suit_array)
#             covariate_id_list.append('LR')
# =============================================================================
        
        elif crop_id == 'AV':
            
            LT_array_dict = dict.fromkeys(['s','o','n'])
            LX_array_dict = dict.fromkeys(['s','o','n'])
            
            for rst in suit_raster_list:
                cova_indicator = rst.split('\\')[-1].split('_')[2][:2]
                month_indicator = rst.split('\\')[-1].split('_')[2][2]
                
                if cova_indicator == 'LT':
                    if month_indicator == 'S':
                        LT_array_dict['s'] = raster.getRasterArray(rst)
                    elif month_indicator == 'O':
                        LT_array_dict['o'] = raster.getRasterArray(rst)
                    elif month_indicator == 'N':
                        LT_array_dict['n'] = raster.getRasterArray(rst)
                elif cova_indicator == 'LX':
                    if month_indicator == 'S':
                        LX_array_dict['s'] = raster.getRasterArray(rst)
                    elif month_indicator == 'O':
                        LX_array_dict['o'] = raster.getRasterArray(rst)
                    elif month_indicator == 'N':
                        LX_array_dict['n'] = raster.getRasterArray(rst)
                else:
                    suit_array = raster.getRasterArray(rst)
                    suit_array_stack.append(suit_array)
                    suit_array = np.where(suit_array==1, 20, np.where(suit_array==2,10,0))
                    suit_array = np.where(suit_array==20, 2, np.where(suit_array==10,1,0))
                    overall_suit_array = overall_suit_array + suit_array
                    covariate_id_list.append(rst.split('\\')[-1].split('_')[2].split('.')[0])
                    
#           NIWA rule is different from Tasmanian rule. 2 represent optimal, 1 represent marginal, 
#           and 0 represent not suitable. the overall suitability is the sum of the suitability level of
#           each layer. the higher the more suitable
            lt_suit_array = np.where(np.logical_and(np.logical_and(LT_array_dict['s']==1, 
                                                                   LT_array_dict['o']==1), 
                                                    LT_array_dict['n']==1), 2, 
                                     np.where(np.logical_and(np.logical_and(np.logical_or(LT_array_dict['s']==2, LT_array_dict['s']==1), 
                                                                            np.logical_or(LT_array_dict['o']==2, LT_array_dict['o']==1)), 
                                                             LT_array_dict['n']==1), 1, 
                                     0))
            lx_suit_array = np.where(np.logical_and(np.logical_and(LX_array_dict['s']==1, 
                                                                   LX_array_dict['o']==1), 
                                                    LX_array_dict['n']==1), 2, 
                                     np.where(np.logical_and(np.logical_and(np.logical_or(LX_array_dict['s']==2, LX_array_dict['s']==1), 
                                                                            np.logical_or(LX_array_dict['o']==2, LX_array_dict['o']==1)), 
                                                             LX_array_dict['n']==1), 1, 
                                     0))        
            
            lt_suit_array[np.where(LT_array_dict['s'] == self.no_data)] = self.no_data
            suit_array_stack.append(lt_suit_array)
            
            raster.array2Raster(lt_suit_array, ref_rst, join(out_dir, 'suitability_{}_LT.tif'.format(crop_id)))
            overall_suit_array = overall_suit_array + lt_suit_array
            covariate_id_list.append('LT')
            
            lx_suit_array[np.where(LX_array_dict['s'] == self.no_data)] = self.no_data
            suit_array_stack.append(lx_suit_array)
            
            raster.array2Raster(lx_suit_array, ref_rst, join(out_dir, 'suitability_{}_LX.tif'.format(crop_id)))
            overall_suit_array = overall_suit_array + lx_suit_array
            covariate_id_list.append('LX')
            
        elif crop_id == 'TF':
            for rst in suit_raster_list:

                suit_array = raster.getRasterArray(rst)
                suit_array_stack.append(suit_array)
                suit_array = np.where(suit_array==1, 20, np.where(suit_array==2,10,0))
                suit_array = np.where(suit_array==20, 2, np.where(suit_array==10,1,0))
                overall_suit_array = overall_suit_array + suit_array
                covariate_id_list.append(rst.split('\\')[-1].split('_')[2].split('.')[0])
            
            
            
        # here is to calculate the overall suitability
#        if len(suit_array_stack) > 0:
#            crop_suit_array = ExtractMaxValueOfStack(suit_array_stack)
        ref_array = homogenize_nodata_area(suit_array_stack, self.no_data)
        overall_suit_array[np.where(ref_array == self.no_data)] = self.no_data
        crop_suit_raster = join(out_dir, '{}_suitability.tif'.format(crop_id))
        raster.array2Raster(overall_suit_array, ref_rst, crop_suit_raster)
            
#            print('create dominant worst covariate raster at {}...'.format(dt.datetime.now()))
#            worst_dominant_array, worst_count_array, worst_dominant_legend_list = ExtractMaxValueIndexBinaryOfStack(suit_array_stack, covariate_id_list, 4)
#            
#            worst_dominant_array[np.where(ref_array == self.no_data)] = self.no_data
#            worst_dominant_raster_file = join(out_dir, '{}_worst_dominant.tif'.format(crop_id))
#            raster.array2Raster(worst_dominant_array, ref_rst, worst_dominant_raster_file)
#            
#            worst_count_array[np.where(ref_array == self.no_data)] = self.no_data
#            worst_count_raster_file = join(out_dir, '{}_worst_count.tif'.format(crop_id))
#            raster.array2Raster(worst_count_array, ref_rst, worst_count_raster_file)
#            
#            worst_dominant_legend_csv = join(out_dir, '{}_worst_dominant_legend.csv'.format(crop_id))
#            csvw = CSVOperation.CSVWriting()
#            headers = ['raster value', 'number of restriction', 'covariates']
#            csvw.WriteLines(worst_dominant_legend_csv, headers, worst_dominant_legend_list)
#        else:
#            print('Warning! No suitability map for {} was created!'.format(crop_id))

    def mapping_weighted_rule(self, crop_id, covariate_rasters, conn, covariate_root_dir, suit_root_dir):
        
        raster = Raster()
        self.no_data =raster.getNoDataValue(covariate_rasters[-1])
        ref_rst = covariate_rasters[-1]
        covariate_id_list = []
        suit_array_stack = []
        suit_raster_list = []
#        overall_suit_array = np.zeros(raster.getRasterArray(ref_rst).shape)
        
        filepath = strip_end(ref_rst, ref_rst.split('\\')[-1])
        out_dir = join(suit_root_dir, strip_start(filepath, covariate_root_dir)[1:]) # the [1:] is for removing the first and the last '\' of string
        
        if not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok = True)
         
        
        for rst in covariate_rasters:
            
            filename = rst.split('\\')[-1].split('.')[0]
            
            if len(filename.split('_')) == 1:
                covariate_id = filename
#                covariate_id_list.append(covariate_id)
                out_raster = join(out_dir, 'suitability_{}_{}.tif'.format(crop_id, covariate_id))
            else:

                covariate_id = filename.split('_')[1]
#                covariate_id_list.append(covariate_id)
                time_span = '{}_{}'.format(filename.split('_')[-2], filename.split('_')[-1])
                out_raster = join(out_dir, 'suitability_{}_{}_{}.tif'.format(crop_id, covariate_id, time_span))
            
            suit_raster_list.append(out_raster)
                
            with conn as cur:
                rows = cur.execute("select * from suitability_rule where crop_id=? and covariate_id=? order by suitability_level", (crop_id,covariate_id,)).fetchall()
                is_continual = cur.execute("select * from Covariate where id=?", (covariate_id,)).fetchone()['iscontinual']
                
                
            # If the query returns none then move to the next covariate
            if rows:
                covariate_array = raster.getRasterArray(rst)  # array of the covariate
                
                if is_continual == 1:
                    suit_array = self.__reclassify_contianual__(covariate_array, rows)
                else:
                    suit_array = self.__reclassify_catorgorical__(covariate_array, rows)
                
#                suit_array = suit_array / weight
                suit_array[np.where(covariate_array == self.no_data)] = self.no_data
                
                raster.array2Raster(suit_array, ref_rst, out_raster)
                
#                suit_array_stack.append(suit_array)
            else:
                print('Warning! Suitability ruleset for {}, {} not found! Please check the database.'.format(crop_id, covariate_id))
        
        
# =============================================================================
#**************The special funtions for AV and HM based on NIWA's rule were commented out because PFR introduced new rules for them, which is consistent to other crops.
#         if crop_id == 'HM':
#             
#             HT_array_dict = dict.fromkeys(['s','u','a','w'])
#             LM_array_dict = dict.fromkeys(['s','u','a','w'])
#             LR_array_dict = dict.fromkeys(['s','u','a','w'])
#             
#             for rst in suit_raster_list:
#                 cova_indicator = rst.split('\\')[-1].split('_')[2][:2]
#                 season_indicator = rst.split('\\')[-1].split('_')[2][2]
#                 
#                 if cova_indicator == 'HT':
#                     if season_indicator == 'S':
#                         HT_array_dict['s'] = raster.getRasterArray(rst)
#                     elif season_indicator == 'U':
#                         HT_array_dict['u'] = raster.getRasterArray(rst)
#                     elif season_indicator == 'A':
#                         HT_array_dict['a'] = raster.getRasterArray(rst)
#                     elif season_indicator == 'W':
#                         HT_array_dict['w'] = raster.getRasterArray(rst)
#                 elif cova_indicator == 'LM':
#                     if season_indicator == 'S':
#                         LM_array_dict['s'] = raster.getRasterArray(rst)
#                     elif season_indicator == 'U':
#                         LM_array_dict['u'] = raster.getRasterArray(rst)
#                     elif season_indicator == 'A':
#                         LM_array_dict['a'] = raster.getRasterArray(rst)
#                     elif season_indicator == 'W':
#                         LM_array_dict['w'] = raster.getRasterArray(rst)
#                 elif cova_indicator == 'LR':
#                     if season_indicator == 'S':
#                         LR_array_dict['s'] = raster.getRasterArray(rst)
#                     elif season_indicator == 'U':
#                         LR_array_dict['u'] = raster.getRasterArray(rst)
#                     elif season_indicator == 'A':
#                         LR_array_dict['a'] = raster.getRasterArray(rst)
#                     elif season_indicator == 'W':
#                         LR_array_dict['w'] = raster.getRasterArray(rst)
#             
#                 else:
#                     suit_array = raster.getRasterArray(rst)
#                     suit_array_stack.append(suit_array)
# #                    suit_array = np.where(suit_array==1, 20, np.where(suit_array==2,10,0))
# #                    suit_array = np.where(suit_array==20, 2, np.where(suit_array==10,1,0))
# #                    overall_suit_array = overall_suit_array + suit_array
#                     covariate_id_list.append(rst.split('\\')[-1].split('_')[2].split('.')[0])
#             
#             ht_suit_array = np.where(np.logical_or(np.logical_or(np.logical_or(HT_array_dict['s']==4, 
#                                                                                HT_array_dict['u']==4), 
#                                                                  HT_array_dict['a']==4), 
#                                                    HT_array_dict['w']==4), 4, self.no_data)
#             ht_suit_array = np.where(np.logical_and(np.logical_or(np.logical_or(np.logical_or(HT_array_dict['s']==3,
#                                                                                               HT_array_dict['u']==3),
#                                                                                 HT_array_dict['a']==3), 
#                                                                   HT_array_dict['w']==3), 
#                                                     ht_suit_array != 4), 3, ht_suit_array)
#             ht_suit_array = np.where(np.logical_and(np.logical_and(np.logical_or(np.logical_or(np.logical_or(HT_array_dict['s']==2,
#                                                                                                              HT_array_dict['u']==2),
#                                                                                                HT_array_dict['a']==2), 
#                                                                                  HT_array_dict['w']==2), 
#                                                                    ht_suit_array != 4), 
#                                                     ht_suit_array != 3), 2, ht_suit_array)                    
#             ht_suit_array = np.where(np.logical_and(np.logical_and(ht_suit_array != 4, 
#                                                                    ht_suit_array != 3),
#                                                     ht_suit_array != 2), 1, ht_suit_array)
#             
#             ht_suit_array[np.where(HT_array_dict['s'] == self.no_data)] = self.no_data
#             raster.array2Raster(ht_suit_array, ref_rst, join(out_dir, 'suitability_{}_HT.tif'.format(crop_id)))
#             suit_array_stack.append(ht_suit_array)
#             covariate_id_list.append('HT')
#                     
#             
#             lm_suit_array = np.where(np.logical_or(np.logical_or(np.logical_or(LM_array_dict['s']==4, 
#                                                                                LM_array_dict['u']==4), 
#                                                                  LM_array_dict['a']==4), 
#                                                    LM_array_dict['w']==4), 4, self.no_data)
#             lm_suit_array = np.where(np.logical_and(np.logical_or(np.logical_or(np.logical_or(LM_array_dict['s']==3,
#                                                                                               LM_array_dict['u']==3),
#                                                                                 LM_array_dict['a']==3), 
#                                                                   LM_array_dict['w']==3), 
#                                                     lm_suit_array != 4), 3, lm_suit_array)
#             lm_suit_array = np.where(np.logical_and(np.logical_and(np.logical_or(np.logical_or(np.logical_or(LM_array_dict['s']==2,
#                                                                                                              LM_array_dict['u']==2),
#                                                                                                LM_array_dict['a']==2), 
#                                                                                  LM_array_dict['w']==2), 
#                                                                    lm_suit_array != 4), 
#                                                     lm_suit_array != 3), 2, lm_suit_array)                    
#             lm_suit_array = np.where(np.logical_and(np.logical_and(lm_suit_array != 4, 
#                                                                    lm_suit_array != 3),
#                                                     lm_suit_array != 2), 1, lm_suit_array)
#             
#             lm_suit_array[np.where(LM_array_dict['s'] == self.no_data)] = self.no_data
#             raster.array2Raster(lm_suit_array, ref_rst, join(out_dir, 'suitability_{}_LM.tif'.format(crop_id)))
#             suit_array_stack.append(lm_suit_array)
#             covariate_id_list.append('LM')
#                     
# # =============================================================================
# #             lr_suit_array = np.where(np.logical_and(np.logical_and(np.logical_and(LR_array_dict['s']==1, 
# #                                                                                   LR_array_dict['u']==1), 
# #                                                                    LR_array_dict['a']==1), 
# #                                                     LR_array_dict['w']==1), 1, 
# #                                      np.where(np.logical_and(np.logical_and(np.logical_and(LR_array_dict['s']==2, 
# #                                                                                            LR_array_dict['u']==2), 
# #                                                                             LR_array_dict['a']==2), 
# #                                                              LR_array_dict['w']==2), 2, 
# #                                      4))
# #             
# #             lr_suit_array[np.where(covariate_array == self.no_data)] = self.no_data
# #             raster.array2Raster(lr_suit_array, ref_rst, join(out_dir, 'suitability_{}_LR.tif'.format(crop_id)))
# #             suit_array_stack.append(lr_suit_array)
# #             covariate_id_list.append('LR')
# # =============================================================================
#       
#         elif crop_id == 'AV':
#             
#             LT_array_dict = dict.fromkeys(['s','o','n'])
#             LX_array_dict = dict.fromkeys(['s','o','n'])
#             
#             for rst in suit_raster_list:
#                 cova_indicator = rst.split('\\')[-1].split('_')[2][:2]
#                 month_indicator = rst.split('\\')[-1].split('_')[2][2]
#                 
#                 if cova_indicator == 'LT':
#                     if month_indicator == 'S':
#                         LT_array_dict['s'] = raster.getRasterArray(rst)
#                     elif month_indicator == 'O':
#                         LT_array_dict['o'] = raster.getRasterArray(rst)
#                     elif month_indicator == 'N':
#                         LT_array_dict['n'] = raster.getRasterArray(rst)
#                 elif cova_indicator == 'LX':
#                     if month_indicator == 'S':
#                         LX_array_dict['s'] = raster.getRasterArray(rst)
#                     elif month_indicator == 'O':
#                         LX_array_dict['o'] = raster.getRasterArray(rst)
#                     elif month_indicator == 'N':
#                         LX_array_dict['n'] = raster.getRasterArray(rst)
#                 else:
#                     suit_array = raster.getRasterArray(rst)
#                     suit_array_stack.append(suit_array)
# #                    suit_array = np.where(suit_array==1, 20, np.where(suit_array==2,10,0))
# #                    suit_array = np.where(suit_array==20, 2, np.where(suit_array==10,1,0))
# #                    overall_suit_array = overall_suit_array + suit_array
#                     covariate_id_list.append(rst.split('\\')[-1].split('_')[2].split('.')[0])
#                     
# #           NIWA rule is different from Tasmanian rule. 2 represent optimal, 1 represent marginal, 
# #           and 0 represent not suitable. the overall suitability is the sum of the suitability level of
# #           each layer. the higher the more suitable
#             
#             
#             lt_suit_array = np.where(np.logical_or(np.logical_or(LT_array_dict['s']==4, 
#                                                                  LT_array_dict['o']==4), 
#                                                    LT_array_dict['n']==4), 4, self.no_data)
#             lt_suit_array = np.where(np.logical_and(np.logical_or(np.logical_or(LT_array_dict['s']==3,
#                                                                                 LT_array_dict['o']==3),
#                                                                   LT_array_dict['n']==3),
#                                                     lt_suit_array != 4), 3, lt_suit_array)
#             lt_suit_array = np.where(np.logical_and(np.logical_and(np.logical_or(np.logical_or(LT_array_dict['s']==2,
#                                                                                                LT_array_dict['o']==2),
#                                                                                  LT_array_dict['n']==2),
#                                                                    lt_suit_array != 4), 
#                                                     lt_suit_array != 3), 2, lt_suit_array)                    
#             lt_suit_array = np.where(np.logical_and(np.logical_and(lt_suit_array != 4, 
#                                                                    lt_suit_array != 3),
#                                                     lt_suit_array != 2), 1, lt_suit_array)
#                                 
#             
#             lt_suit_array[np.where(LT_array_dict['s'] == self.no_data)] = self.no_data
#             suit_array_stack.append(lt_suit_array)
#             raster.array2Raster(lt_suit_array, ref_rst, join(out_dir, 'suitability_{}_LT.tif'.format(crop_id)))
#             covariate_id_list.append('LT')                    
#             
# 
#                                 
#             lx_suit_array = np.where(np.logical_or(np.logical_or(LX_array_dict['s']==4, 
#                                                                  LX_array_dict['o']==4), 
#                                                    LX_array_dict['n']==4), 4, self.no_data)
#             lx_suit_array = np.where(np.logical_and(np.logical_or(np.logical_or(LX_array_dict['s']==3,
#                                                                                 LX_array_dict['o']==3),
#                                                                   LX_array_dict['n']==3),
#                                                     lx_suit_array != 4), 3, lx_suit_array)
#             lx_suit_array = np.where(np.logical_and(np.logical_and(np.logical_or(np.logical_or(LX_array_dict['s']==2,
#                                                                                                LX_array_dict['o']==2),
#                                                                                  LX_array_dict['n']==2),
#                                                                    lx_suit_array != 4), 
#                                                     lx_suit_array != 3), 2, lx_suit_array)                    
#             lx_suit_array = np.where(np.logical_and(np.logical_and(lx_suit_array != 4, 
#                                                                    lx_suit_array != 3),
#                                                     lx_suit_array != 2), 1, lx_suit_array)                    
#                                       
# 
#             lx_suit_array[np.where(LX_array_dict['s'] == self.no_data)] = self.no_data
#             suit_array_stack.append(lx_suit_array)
#             raster.array2Raster(lx_suit_array, ref_rst, join(out_dir, 'suitability_{}_LX.tif'.format(crop_id)))
#             covariate_id_list.append('LX')
# =============================================================================
        if crop_id == '': # this "if" is just to replace the commented "if" above
            pass
        else:
            for rst in suit_raster_list:

                suit_array = raster.getRasterArray(rst)
                suit_array_stack.append(suit_array)
                covariate_id_list.append(rst.split('\\')[-1].split('_')[2].split('.')[0])
            
            
            
        # here is to calculate the overall suitability
        if len(suit_array_stack) > 0:
#            crop_suit_array = WeightedSum(crop_id, suit_array_stack, covariate_id_list, conn)
            crop_suit_array = WeightedSum_limit(crop_id, suit_array_stack, covariate_id_list, conn)
            
            ref_array = homogenize_nodata_area(suit_array_stack, self.no_data)
            crop_suit_array[np.where(ref_array == self.no_data)] = self.no_data
            crop_suit_raster = join(out_dir, '{}_suitability.tif'.format(crop_id))
            raster.array2Raster(crop_suit_array, ref_rst, crop_suit_raster)
            
            print('create dominant worst covariate raster at {}...'.format(dt.datetime.now()))
            worst_dominant_array, worst_count_array, worst_dominant_legend_list = ExtractMaxValueIndexBinaryOfStack(suit_array_stack, covariate_id_list, 4)
            
            worst_dominant_array[np.where(ref_array == self.no_data)] = self.no_data
            worst_dominant_raster_file = join(out_dir, '{}_worst_dominant.tif'.format(crop_id))
            raster.array2Raster(worst_dominant_array, ref_rst, worst_dominant_raster_file)
            
            worst_count_array[np.where(ref_array == self.no_data)] = self.no_data
            worst_count_raster_file = join(out_dir, '{}_worst_count.tif'.format(crop_id))
            raster.array2Raster(worst_count_array, ref_rst, worst_count_raster_file)
            
            worst_dominant_legend_csv = join(out_dir, '{}_worst_dominant_legend.csv'.format(crop_id))
            csvw = CSVOperation.CSVWriting()
            headers = ['raster value', 'number of restriction', 'covariates']
            csvw.WriteLines(worst_dominant_legend_csv, headers, worst_dominant_legend_list)
        else:
            print('Warning! No suitability map for {} was created!'.format(crop_id))
        
        
        
        
def get_cova_raster_list(crop, root_dir, covariate_id_list_of_crop):
    
    has_climate = False
    covariate_rasters = []
    for (dirpath, subdirname, filenames) in walk(root_dir):
        if dirpath == root_dir:  # get all the raster under root dir which are share used covariate raster such as slope, ph etc.. 
            for f in filenames:
                if f.split('.')[-1].lower()[:3] == 'tif' and f.split('.')[0] in covariate_id_list_of_crop :
                    covariate_rasters.append(join(dirpath, f))
                    
        if dirpath.split('\\')[-1] == crop:
            for f in filenames:
                if f.split('.')[-1].lower()[:3] == 'tif':
                    covariate_rasters.append(join(dirpath, f))
                    has_climate = True
            break
    return covariate_rasters, has_climate


def get_cova_raster_list_new(crop, root_dir, covariate_id_list_of_crop):
    
    covariate_rasters = []
    for (dirpath, subdirname, filenames) in walk(root_dir):
        if dirpath == root_dir:  # get all the raster under root dir which are share used covariate raster such as slope, ph etc.. 
            for f in filenames:

                if f.split('.')[-1].lower()[:3] == 'tif':
                    if f.split('.')[0] in covariate_id_list_of_crop or (len(f)>7 and f.split('_')[1] in covariate_id_list_of_crop):
                        covariate_rasters.append(join(dirpath, f))
                    
            break
    return covariate_rasters


def main():    
    
    conf = r'config.ini'
    
    config_params = ConfigParameters(conf)
    proj_header = 'projectConfig'
#    sui_header = 'landSuitability'
    
    db_file = config_params.GetDB(proj_header)
    covariates_dir = config_params.GetProcessedCovariateDir(proj_header)
    suit_map_dir = config_params.GetSuitabilityParams(proj_header)
    
    if not os.path.exists(covariates_dir):
        sys.exit('The directory of cofiguration files "{}" does not exist.'.format(covariates_dir))
    
    
    conn = Sqlite_connection(db_file)
    
    crops_id = []
    crops = []
    
    with conn as cur:
        rows = cur.execute("select * from crop").fetchall()
        
    for row in rows:
        crops_id.append(row['id'])
        crops.append(row['crop'])
    
    landsuit = LandSuitability()
    
    for crop_id, crop in zip(crops_id, crops):
        
        if crop_id != 'KM':
            continue
        
        covariate_id_list_of_crop = []
        print('Processing {} at {}.'.format(crop, dt.datetime.now()))
        
        with conn as cur:
            rows = cur.execute("select distinct covariate_id from suitability_rule where crop_id=?", (crop_id,)).fetchall()
        
        for row in rows:
            covariate_id_list_of_crop.append(row['covariate_id'])
        
        
        for (subdirpath, subdirname, filenames) in walk(covariates_dir):
            for f in filenames:
                if f == 'OID.tif':
                    print('{}   --   {}.'.format(subdirpath, dt.datetime.now()))
                    
                    covariate_rasters = get_cova_raster_list_new(crop, subdirpath, covariate_id_list_of_crop)
                    
                    dirnames = subdirpath.split('\\')
                    
                    if len(covariate_rasters) > 0:
                        
                        suit_dir = join(suit_map_dir, dirnames[-2], dirnames[-1])
                        
                        landsuit.mapping(crop_id, crop, covariate_rasters, conn, covariates_dir, suit_dir)
                    else:
                        print('Warning! Covariate raster for {} not found!'.format(crop))
                        
                    continue
    
    print('End at {}.'.format(dt.datetime.now()))
    
    
if __name__ == '__main__':
    
    main()    
    
    
        
        
        
        
        
        
        
    