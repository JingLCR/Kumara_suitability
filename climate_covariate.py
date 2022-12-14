# -*- coding: utf-8 -*-
"""
Created on Mon Jul  2 16:28:00 2018

@author: guoj
"""

import numpy as np
import datetime as dt
import os.path
from os.path import join
from os import walk

from raster import Raster



class ExtractTimeInfo(object):
    '''
    Extract an unique 'Year' list from a directory, and extract an unique 'Date' list based on input year. 
    '''
    def __init__(self, path):
        self.path = path
        self.file = []

        for (dirpath, dirnames, filenames) in walk(self.path):
            self.file.extend(filenames)
            break
        
    def extractYears(self):
        years = sorted(list(set([y.split('-')[0] for y in self.file])))
        return years
    
    def extractMonths(self, year):
        months = sorted(list(set([m.split('-')[1] for m in self.file if m.split('-')[0] == year])))
        return months
    
    def extractDates(self, year, month=None): 
        if month is None:
            dates = sorted(list(d.split('.')[0] for d in self.file if d.split('-')[0] == year and d.split('.')[-1] == 'tif'))
        else:
            dates = sorted(list(d.split('.')[0] for d in self.file if d.split('-')[0] == year and d.split('-')[1] == month and d.split('.')[-1] == 'tif'))
        return dates

class ExtractTimeInfo2(ExtractTimeInfo): 
    
    def __init__(self, file_list):
        self.file = file_list
        
    def extractMonths(self, year):
        months = sorted(list(set([m.split('\\')[-1].split('-')[1] for m in self.file if m.split('\\')[-1].split('-')[0] == year])))
        return months
    
class ClimaticCovariates(object):
    '''
    Climatic covariates class
    '''
    def __init__(self, year_list, data_dir):
        '''
        year_list: a numeric list of years which are took into account when calculating
                   climatic covariates
        '''  
        def GetRefRaster(data_dir):
            for (subdirpath, subdirname, filenames) in walk(data_dir):
                for f in filenames:
                    if f.split('.')[-1].lower()[:3] == 'tif':
                        return join(subdirpath, f)
        
        self.years = year_list
        self.dir = data_dir
        self.raster = Raster()
        self.ref_raster = GetRefRaster(self.dir)
        self.ref_array = self.raster.getRasterArray(self.ref_raster)
        self.no_data = self.raster.getNoDataValue(self.ref_raster)


    def __GetFileList__(self, start_date, end_date, keyword):
        '''
        Return a file list for the given period of the years.
        'keyword' is the key to look for the correct files. 
        Based on the file/folder structure of Climate data, 
        here assumes one of the subfolder should contain the keyword. 
        '''
        files = []
        for (subdirpath, subdirname, filenames) in walk(self.dir):
            if keyword in subdirpath.split('\\')[-1]:    
                for f in filenames:
                    # get the date of each file
                    d = f.split('.')[0].split('-')
                    # if the month of the start date is later than that of the end date
                    # which means the given period is across two natural years
                    if int(start_date[:2]) > int(end_date[:2]): 
                        for y in self.years[:-1]:
                            if (        # in that case
                                    (   # get files of that year
                                        (d[0] == y) and 
                                        (   # and the date after the start date
                                            (d[1] == start_date[:2] and int(d[-1]) >= int(start_date[-2:])) or 
                                            (int(d[1]) > int(start_date[:2])) 
                                        )
                                    ) 
                                    or  
                                    (   # also get files of the next year
                                        (int(d[0]) == int(y)+1) and
                                        (   # and the date before the end date
                                            (d[1] == end_date[:2] and int(d[-1]) <= int(end_date[-2:])) or 
                                            (int(d[1]) < int(end_date[:2]))            
                                        )
                                    )
                                ):
                                
                                files.append(join(subdirpath, f))
                    else: # the given period in one natural year
                        for y in self.years:
                            if (    # get files of that year
                                    (d[0] == y) and 
                                    (   # and the date in between the start and the end date
                                        (d[1] == start_date[:2] and int(d[-1]) >= int(start_date[-2:])) or 
                                        (int(d[1]) > int(start_date[:2]) and int(d[1]) < int(end_date[:2])) or
                                        (d[1] == end_date[:2] and int(d[-1]) <= int(end_date[-2:]))
                                    )
                                ):
                                
                                files.append(join(subdirpath, f))
        
        return files
    
    
    def __GetFileDictionary__(self, start_date, end_date, keyword):
        '''
        From the file list generated from the __GetFileList__ function,
        return a file Dictionary with year named key and a file list related to the key.
        '''
        file_dict = {}
        file_list = self.__GetFileList__(start_date, end_date, keyword)

        if int(start_date[:2]) > int(end_date[:2]): 
            for year in self.years[:-1]:
                files = []
                for f in file_list:
                    y, m, d = f.split('\\')[-1].split('.')[0].split('-')
                    if (
                            (
                                (y == year) and 
                                (
                                    (m == start_date[:2] and int(d) >= int(start_date[-2:])) or 
                                    (int(m) > int(start_date[:2])) 
                                )
                            ) 
                            or
                            (
                                (int(y) == int(year)+1) and
                                (
                                    (m == end_date[:2] and int(d) <= int(end_date[-2:])) or 
                                    (int(m) < int(end_date[:2]))            
                                )
                            )
                        ):
                        
                        files.append(f)
                file_dict[year] = files
                
        else:
            for year in self.years:
                files = []
                for f in file_list:
                    y, m, d = f.split('\\')[-1].split('.')[0].split('-')
                    if (
                            (y == year) and 
                            (
                                (m == start_date[:2] and int(d) >= int(start_date[-2:])) or 
                                (int(m) > int(start_date[:2]) and int(m) < int(end_date[:2])) or
                                (m == end_date[:2] and int(d) <= int(end_date[-2:]))
                            )
                        ):
                        
                        files.append(f)
                file_dict[year] = files         
        
        return file_dict
        
    def __ChillHoursModel__(self, tmin_array, tmax_array, base_min, base_max):
        '''
        The model of simulating chill hours based on daily temperature data.
        
        *Note: 1. the original model has an issue on the denominator (tave_array - tmin_array) 
                  of the algorithm, when it is equel to 0. 
               2. some pixels of the daily temperature data have abnormal values e.g. 
                  the min is greater than the max (e.g. pixel [43, 180] from 1971-05-01).
               So in this function a reset (when abnormal values occur) of min temperature is 
               coded at the beginning, to eliminate the effect. But this may result in other 
               issues such as an unexpected result.
               
               3. When negtive chill hours occur set it to 0 (may not the correct way)
        '''
        tmin_array = np.where(tmin_array >= tmax_array, tmax_array - 1, tmin_array)
        tave_array = (tmin_array + tmax_array) / 2
        daychill_array_A =  np.where(tmax_array > base_max, 2 * 6 * (base_max - tmin_array) / (tave_array - tmin_array), 24)
        daychill_array_B = np.where(tmin_array < base_min, 2 * 6 *(base_min - tmin_array) / (tave_array - tmin_array), 0)
        
        daychill_array = daychill_array_A - daychill_array_B
        daychill_array = np.where(daychill_array > 0, daychill_array, 0)
        
        return daychill_array
    

class AnnualExtremeTemperatureFrequency(ClimaticCovariates):
    
        
    '''
    Temperatrue Frequency includes frost risk frequency and max daily temperature etc. 
    It is determined by counting years that had at least 1 day of extreme temperature 
    occuring at less than the threshold temperature between a certain period in an 
    agriculture year. 
    This function returns a raster array of the frequency within one agriculture year, 
    but it can be called multiple times to get an average frequency of multiple years.
    
    annual_file_list: a file list contains the daily temperature file in a certain 
                      period when frost risk is matter in an agriculture year
    base_temp:        the temperature threshold of selected crop to determine
                      the occurance of frost risk (compared with the base temperature)
    direction:        a keyword which is either 'above' or 'below' to determine 
                      the temperature interval that exceeds the base temperature
    '''
    
    direction = ''
    thres_num_days = 0
    
    def create_array(self, t1_key, start_date, end_date, base_temp):    
        
        t1_dict = self.__GetFileDictionary__(start_date, end_date, t1_key)
        total_years = len(t1_dict)
        
        covariate_array = np.zeros(self.ref_array.shape)
    
        for year in t1_dict:
            annual_file_list = t1_dict[year]
            accumu_daily_array = np.zeros(self.ref_array.shape)
            for f in annual_file_list:
                raster_array = self.raster.getRasterArray(f)
                if self.direction == 'below':
                    daily_array = np.where(raster_array < base_temp, 1, 0) 
                elif self.direction == 'above':
                    daily_array = np.where(raster_array > base_temp, 1, 0) 
                else:
                    break
                
                accumu_daily_array = accumu_daily_array + daily_array
            
            annual_frequency_array = np.where(accumu_daily_array > self.thres_num_days, 1, 0)
            
            covariate_array = covariate_array + annual_frequency_array 
            
        covariate_array = covariate_array / total_years
        covariate_array = np.where(self.ref_array == self.no_data, self.no_data, covariate_array)
       
        return covariate_array
    
    
class AnnualFrostRiskFrequency(AnnualExtremeTemperatureFrequency):
    
    direction = 'below'

class AnnualMaxDailyTemperatureFrequency(AnnualExtremeTemperatureFrequency):    
    
    direction = 'above'
    
class AnnualMinDailyTemperatureFrequencyAbove(AnnualExtremeTemperatureFrequency):    
    
    direction = 'above'   
    

class AnnualGDD(ClimaticCovariates):
    
    '''
    Growing Degree Days (GDD) is quantified for each day to give a GDD unit and
    is calculated by taking the average of the daily maximum and minmum temperatures
    compared to a base temperature. This function returns a raster array of the GDD
    within one agriculture year, but it can be called multiple times to get an average 
    GDD of multiple years.
    
    annual_file_list_min: a file list contains the daily min temperature file in a certain 
                          period when GDD is matter in an agriculture year
    annual_file_list_max: a file list contains the daily max temperature file in a certain 
                          period when GDD is matter in an agriculture year
    base_temp:            the base temperature of selected crop to quantify GDD
    '''
    
    def create_array(self,  t1_key, t2_key, start_date, end_date, base_temp):
        
        t1_dict = self.__GetFileDictionary__(start_date, end_date, t1_key)
        total_years = len(t1_dict)
        t2_dict = self.__GetFileDictionary__(start_date, end_date, t2_key)
        
        covariate_array = np.zeros(self.ref_array.shape)
    
        for year in t1_dict:
            annual_file_list_min = t1_dict[year]
            annual_file_list_max = t2_dict[year]
            accumu_daily_array = np.zeros(self.ref_array.shape)
            for minf, maxf in zip(annual_file_list_min, annual_file_list_max):
                min_raster_array = self.raster.getRasterArray(minf)
                max_raster_array = self.raster.getRasterArray(maxf)
                daily_array = (min_raster_array + max_raster_array) / 2 - base_temp
                daily_array = np.where(daily_array<=0, 0, daily_array)                       
                accumu_daily_array = accumu_daily_array + daily_array
                
            covariate_array = covariate_array + accumu_daily_array 
            
        covariate_array = covariate_array / total_years
        covariate_array = np.where(self.ref_array == self.no_data, self.no_data, covariate_array)
        
        return covariate_array
    
    
class AnnualChillHours(ClimaticCovariates): 
    
    '''
    Chill hours are calculated as the number of hours in 
    a temperature range of (threshold_tmp_min to threshold_tmp_max).
    This count was summed and divided by the total number years.
    
    *Note: As the hourly temperature data is not available, we use to daily data to model 
           chill hours (with '__ChillHoursModel__' function).The model is provided by 
           Anne-Gaelle Ausseil (from Winterchillhours_HB.rmd) 
    
    annual_file_list_min: a file list contains the daily min temperature file in a certain 
                          period when chill hours is matter in an agriculture year
    annual_file_list_max: a file list contains the daily max temperature file in a certain 
                          period when chill hours is matter in an agriculture year
    base_temp_min:        the min base temperature threshold of selected crop to calculate 
                          chill hours
    base_temp_max:        the max base temperature threshold of selected crop to calculate 
                          chill hours
    '''
    
    def create_array(self, t1_key, t2_key, start_date, end_date, base_temp_min, base_temp_max):
        
        t1_dict = self.__GetFileDictionary__(start_date, end_date, t1_key)
        total_years = len(t1_dict)
        t2_dict = self.__GetFileDictionary__(start_date, end_date, t2_key)
        
        covariate_array = np.zeros(self.ref_array.shape)
        
        for year in t1_dict:
            annual_file_list_min = t1_dict[year]
            annual_file_list_max = t2_dict[year]
            accumu_daily_array = np.zeros(self.ref_array.shape)
            for minf, maxf in zip(annual_file_list_min, annual_file_list_max):
                min_raster_array = self.raster.getRasterArray(minf)
                max_raster_array = self.raster.getRasterArray(maxf)
                daily_array = self.__ChillHoursModel__(min_raster_array, max_raster_array, base_temp_min, base_temp_max)                        
                accumu_daily_array = accumu_daily_array + daily_array
            
            covariate_array = covariate_array + accumu_daily_array 
            
        covariate_array = covariate_array / total_years
        covariate_array = np.where(self.ref_array == self.no_data, self.no_data, covariate_array)
        
        return covariate_array
    
class AnnualMeanDaily(ClimaticCovariates):    
    
    '''
    Annual mean daily temperature
    '''
    
    def create_array(self, t1_key, start_date, end_date):
        
        '''
        If the t1_key is MinTemp, it will calculate the average daily min temperature
        If the t1_key is MaxTemp, it will calculate the average daily max temperature
        '''
        
        t1_dict = self.__GetFileDictionary__(start_date, end_date, t1_key)
        total_years = len(t1_dict)
        
        covariate_array = np.zeros(self.ref_array.shape)
        
        for year in t1_dict:
            annual_file_list = t1_dict[year]
            annual_average_array = np.zeros(self.ref_array.shape)
            
            for f in annual_file_list:
                raster_array = self.raster.getRasterArray(f)
                annual_average_array = annual_average_array + raster_array
            
            annual_average_array = annual_average_array / len(annual_file_list)
            annual_average_array = annual_average_array - 273.15
            
            covariate_array = covariate_array + annual_average_array 
            
        covariate_array = covariate_array / total_years
        covariate_array = np.where(self.ref_array == self.no_data, self.no_data, covariate_array)
        
        return covariate_array


class MeanTemperature(ClimaticCovariates):
    
    '''
    Mean temperature of certain period of a year (e.g July).
    The difference between this class and the AnnualMeanDaily is this class use averaged daily temperature.
    '''
    
    def create_array(self, t1_key, t2_key, start_date, end_date):     

        
        t1_dict = self.__GetFileDictionary__(start_date, end_date, t1_key)
        t2_dict = self.__GetFileDictionary__(start_date, end_date, t2_key)
        
        total_years = len(t1_dict)
        
        covariate_array = np.zeros(self.ref_array.shape)

        for year in t1_dict:

            annual_file_list_min = t1_dict[year]
            annual_file_list_max = t2_dict[year]
            annual_average_array = np.zeros(self.ref_array.shape)

            
            for minf, maxf in zip(annual_file_list_min, annual_file_list_max):
                
                min_raster_array = self.raster.getRasterArray(minf)
                max_raster_array = self.raster.getRasterArray(maxf)
                    
                mean_raster_array = (min_raster_array + max_raster_array) / 2
                annual_average_array = annual_average_array + mean_raster_array
            
            annual_average_array = annual_average_array / len(annual_file_list_min)
            annual_average_array = annual_average_array - 273.15
            
            covariate_array = covariate_array + annual_average_array 
            
        covariate_array = covariate_array / total_years
        covariate_array = np.where(self.ref_array == self.no_data, self.no_data, covariate_array)
        
        return covariate_array

class MeanExtremeMonthlyTemperature(ClimaticCovariates):    
    
    '''
    Mean monthly temperature (can be min, max or average).
    For the max, first calculate max monthly temperature;
    second, calculate monthly mean in one year 
    (e.g. if the interested months are 2 months, then the accumulated monthly max temperature is divided by 2);
    then get the annual mean based on the number of years.
    
    If we would like to get the monthly min or average, 
    just create a new class that inherit from this one and change the 'method' argument.
    '''
    
    method = ''
    
    def create_array(self, t1_key, start_date, end_date):
        
        t1_dict = self.__GetFileDictionary__(start_date, end_date, t1_key)
        total_years = len(t1_dict)
        
        covariate_array = np.zeros(self.ref_array.shape)
        
        for year in t1_dict:
            annual_file_list = t1_dict[year]
        
            annual_average_array = np.zeros(self.ref_array.shape)
            monthly_accumulated_array = np.zeros(self.ref_array.shape)
            time_info = ExtractTimeInfo2(annual_file_list)
            months = time_info.extractMonths(year)
            
            for m in months:
                i = 0
                for f in annual_file_list:
                    if f.split('\\')[-1].split('-')[1] == m:
                        raster_array = self.raster.getRasterArray(f)
                        if i == 0:
                            target_array = raster_array
                        else:
                            if self.method.lower()[:3] == 'max':
                                target_array = np.maximum(target_array, raster_array)
                            elif self.method.lower()[:3]  == 'min':
                                target_array = np.minimum(target_array, raster_array)
                            elif self.method.lower()[:3]  == 'ave':
                                target_array = np.add(target_array, raster_array)
                            else:
                                print('Warning! No correct array aggregation method was passed to the function "__AnnualMeanMonthlyBasedOnDaily__()". The calculation will the the Max vaule of each array!')
                                target_array = np.maximum(target_array, raster_array)
                        i += 1
                
                if self.method.lower()[:3]  == 'ave':
                    target_array = target_array / (i+1)
                    
                monthly_accumulated_array = monthly_accumulated_array + target_array
            
            annual_average_array = monthly_accumulated_array / len(months)
            annual_average_array = annual_average_array - 273.15
            
            covariate_array = covariate_array + annual_average_array 
            
        covariate_array = covariate_array / total_years
        covariate_array = np.where(self.ref_array == self.no_data, self.no_data, covariate_array)
        
        return covariate_array

class AnnualMeanMaxMonthlyBasedOnDaily(MeanExtremeMonthlyTemperature):
    
    method = 'max'


class ExtremeMonthlyMeanTemperature(ClimaticCovariates):    
    
    '''
    Extreme temperature of multiple months
    '''
    
    method = ''
    
    def create_array(self, t1_key, start_date, end_date):
        
        t1_dict = self.__GetFileDictionary__(start_date, end_date, t1_key)
        total_years = len(t1_dict)
        
        covariate_array = np.zeros(self.ref_array.shape)
        
        for year in t1_dict:
            annual_file_list = t1_dict[year]

            monthly_array = np.zeros(self.ref_array.shape)
            time_info = ExtractTimeInfo2(annual_file_list)
            months = time_info.extractMonths(year)
            
            for m in months:
                i = 0
                for f in annual_file_list:
                    if f.split('\\')[-1].split('-')[1] == m:
                        raster_array = self.raster.getRasterArray(f)
                        monthly_array = monthly_array + raster_array
                        i += 1
                        
                monthly_array = monthly_array / i
                
                if m == months[0]:
                    target_array = monthly_array
                else: 
                    if self.method.lower()[:3] == 'max':
                        target_array = np.maximum(target_array, monthly_array)
                    elif self.method.lower()[:3]  == 'min':
                        target_array = np.minimum(target_array, monthly_array)
                    elif self.method.lower()[:3]  == 'ave':
                        target_array = np.add(target_array, monthly_array)
                    else:
                        print('Warning! No correct array aggregation method was passed to the function "__AnnualMeanMonthlyBasedOnDaily__()". The calculation will the the Max vaule of each array!')
                        target_array = np.maximum(target_array, raster_array)
                
            if self.method.lower()[:3]  == 'ave':
                target_array = target_array / len(months)

            extreme_monthly_array = target_array - 273.15
            covariate_array = covariate_array + extreme_monthly_array 
            
        covariate_array = covariate_array / total_years
        covariate_array = np.where(self.ref_array == self.no_data, self.no_data, covariate_array)
        
        return covariate_array
    
class LowestMonthlyTemperature(ExtremeMonthlyMeanTemperature):
    
    method = 'min'


class AnnualPCP(ClimaticCovariates):
    
    def create_array(self, pcp_key, start_date, end_date):
        
        pcp_dict = self.__GetFileDictionary__(start_date, end_date, pcp_key)
        total_years = len(pcp_dict)
        
        covariate_array = np.zeros(self.ref_array.shape)
        
        for year in pcp_dict:
            annual_file_list = pcp_dict[year]
            annual_array = np.zeros(self.ref_array.shape)
            
            for f in annual_file_list:
                raster_array = self.raster.getRasterArray(f)
                annual_array = annual_array + raster_array
            
            
            covariate_array = covariate_array + annual_array 
            
        covariate_array = covariate_array / total_years
        covariate_array = np.where(self.ref_array == self.no_data, self.no_data, covariate_array)
        
        return covariate_array


class PCPFreqEvery7Days(ClimaticCovariates):
    
    direction = ''
    thres_num_days = 0
    
    def create_array(self, pcp_key, start_date, end_date, base_pcp):
        
        pcp_dict = self.__GetFileDictionary__(start_date, end_date, pcp_key)
        total_years = len(pcp_dict)
        
        covariate_array = np.zeros(self.ref_array.shape)
        
        for year in pcp_dict:
            annual_file_list = pcp_dict[year]
            annual_frequency_array = np.zeros(self.ref_array.shape)
            for i in range(0, len(annual_file_list)):
                if i <= len(annual_file_list) - 7:
                    accumu_daily_array = np.zeros(self.ref_array.shape)
                    for j in range(i,i+7):
                        raster_array = self.raster.getRasterArray(annual_file_list[j])
                        if self.direction == 'below':
                            daily_array = np.where(raster_array <= base_pcp, 1, 0) 
                        elif self.direction == 'above':
                            daily_array = np.where(raster_array >= base_pcp, 1, 0) 
                        else:
                            break
                    
                        accumu_daily_array = accumu_daily_array + daily_array
                    
                    seven_days_pcp_occurrence_array = np.where(accumu_daily_array > self.thres_num_days, 1, 0)
                    
                    annual_frequency_array = annual_frequency_array + seven_days_pcp_occurrence_array
                else:
                    break
                
            annual_frequency_array = np.where(annual_frequency_array > 0, 1, 0)
            covariate_array = covariate_array + annual_frequency_array 
            
        covariate_array = covariate_array / total_years
        covariate_array = np.where(self.ref_array == self.no_data, self.no_data, covariate_array)
       
        return covariate_array

class PCPFreqHarvest(PCPFreqEvery7Days):
    direction = 'above'
    thres_num_days = 3


class FactorFreqInEveryDeterminedConsecutiveDays(ClimaticCovariates):
    
    '''
    Climate factors (temperatrue and rainfall etc), frequency. 
    This can be frost risk frequency and max daily temperature etc..
    It is determined by counting years that have a certain number of 
    days (predifined input) that have extreme climate condition (predifined input)  
    happening in a certain period (consecutive days) (predifined input) in an 
    agriculture year. 
    This class inherits from ClimaticCovariates class.
 
    thres_num_days:  the threshold of number of days when extreme climate condition happens 
                     (extreme condition becomes an issue).
    accu_consc_days: a certain periond of consecutive days (e.g. 7 days)
                     used as a time window to count days when extreme climate condition 
                     happens. E.g. low pcp happens more than 3 days in every 7 days. 
    '''
    
    def __init__(self, year_list, data_dir, direction='', thres_num_days=1, accu_consc_days = 0):
        self.direction = direction
        self.thres_num_days = thres_num_days
        self.accu_consc_days = accu_consc_days
        super(ClimaticCovariates, self).__init__(year_list, data_dir)
    
    
    def create_array(self, climate_key, start_date, end_date, base_climate):
        
        '''
        climate_key:     the key word to determin the climate factor. E.g. tmin, tmax or pcp etc..
        start_date:      the start date of a certain period when the target climate condition is 
                         matter in an agriculture year.
        end_date:        the end date of a certain period when the target climate condition is 
                         matter in an agriculture year. 
        base_climate:    the threshold of climate factor to determine the extreme climate condition.
        
        '''
        
        cli_dict = self.__GetFileDictionary__(start_date, end_date, climate_key)
        total_years = len(cli_dict)
        
        covariate_array = np.zeros(self.ref_array.shape)
        
        for year in cli_dict:
            annual_file_list = cli_dict[year]
            annual_frequency_array = np.zeros(self.ref_array.shape)
            
            if self.accu_consc_days == 0:  # the time window to count extreme climate condition is the whole year
                accumu_daily_array = np.zeros(self.ref_array.shape)
                for f in annual_file_list:
                    raster_array = self.raster.getRasterArray(f)
                    if self.direction == 'below':
                        daily_array = np.where(raster_array < base_climate, 1, 0) 
                    elif self.direction == 'above':
                        daily_array = np.where(raster_array > base_climate, 1, 0) 
                    else:
                        break
                    
                    accumu_daily_array = accumu_daily_array + daily_array
                
                annual_frequency_array = np.where(accumu_daily_array > self.thres_num_days, 1, 0)
                covariate_array = covariate_array + annual_frequency_array 
            
            else:
            
                for i in range(0, len(annual_file_list)):

                    if i <= len(annual_file_list) - self.accu_consc_days:
                        accumu_daily_array = np.zeros(self.ref_array.shape)
                        for j in range(i,i+self.accu_consc_days):
                            raster_array = self.raster.getRasterArray(annual_file_list[j])
                            if self.direction == 'below':
                                daily_array = np.where(raster_array <= base_climate, 1, 0) 
                            elif self.direction == 'above':
                                daily_array = np.where(raster_array >= base_climate, 1, 0) 
                            else:
                                break
                        
                            accumu_daily_array = accumu_daily_array + daily_array
                        
                        n_days_cli_occurrence_array = np.where(accumu_daily_array > self.thres_num_days, 1, 0)
                        annual_frequency_array = annual_frequency_array + n_days_cli_occurrence_array
                    else:
                        break
                    
                annual_frequency_array = np.where(annual_frequency_array > 0, 1, 0)
                covariate_array = covariate_array + annual_frequency_array 
            
        covariate_array = covariate_array / total_years
        covariate_array = np.where(self.ref_array == self.no_data, self.no_data, covariate_array)
       
        return covariate_array


class HeatStressFreq_Onion(FactorFreqInEveryDeterminedConsecutiveDays):
     
    def __init__(self, year_list, data_dir, direction='above', thres_num_days=3, accu_consc_days=0):
        self.direction = direction
        self.thres_num_days = thres_num_days
        self.accu_consc_days = accu_consc_days
        super(FactorFreqInEveryDeterminedConsecutiveDays, self).__init__(year_list, data_dir)
    

class HeatStressFreq_Peas(FactorFreqInEveryDeterminedConsecutiveDays):
     
    def __init__(self, year_list, data_dir, direction='above', thres_num_days=3, accu_consc_days=7):
        self.direction = direction
        self.thres_num_days = thres_num_days
        self.accu_consc_days = accu_consc_days
        super(FactorFreqInEveryDeterminedConsecutiveDays, self).__init__(year_list, data_dir)
        
class HeatStressFreq_Kumara(FactorFreqInEveryDeterminedConsecutiveDays):
     
    def __init__(self, year_list, data_dir, direction='above', thres_num_days=1, accu_consc_days=0):
        self.direction = direction
        self.thres_num_days = thres_num_days
        self.accu_consc_days = accu_consc_days
        super(FactorFreqInEveryDeterminedConsecutiveDays, self).__init__(year_list, data_dir)


class DailyExtremeTemperature(ClimaticCovariates):    
    
    '''
    Extreme (highest or lowest) daily temperature over a certain period of time. 
    '''
    
    method = ''
    
    def create_array(self, t1_key, start_date, end_date):
        
        t1_dict = self.__GetFileDictionary__(start_date, end_date, t1_key)
        total_years = len(t1_dict)
        
        covariate_array = np.zeros(self.ref_array.shape)
        annual_extreme_array = np.zeros(self.ref_array.shape)
        
        for year in t1_dict:
            annual_file_list = t1_dict[year]

            i = 0
            for f in annual_file_list:
                raster_array = self.raster.getRasterArray(f)
                
                if i == 0:
                    target_array = raster_array
                else:
                    if self.method == 'highest':
                        target_array = np.maximum(target_array, raster_array)
                    elif self.method == 'lowest':
                        target_array = np.minimum(target_array, raster_array)
                
                i+=1

            target_array = target_array - 273.15
            annual_extreme_array = annual_extreme_array + target_array

        covariate_array = annual_extreme_array / total_years
        covariate_array = np.where(self.ref_array == self.no_data, self.no_data, covariate_array)
        
        return covariate_array
    
class DailyHighestTemperature(DailyExtremeTemperature):
    
    method = 'highest'
    
class DailyLowestTemperature(DailyExtremeTemperature):
    
    method = 'lowest'


class TotalPercentileRainfall(ClimaticCovariates):
    
    percentile = 50
    condition = ''
    
    def create_array(self, pcp_key, start_date, end_date):
        
        pcp_dict = self.__GetFileDictionary__(start_date, end_date, pcp_key)
        total_years = len(pcp_dict)
        
        covariate_array = np.zeros(self.ref_array.shape)
        
        for year in pcp_dict:
            annual_file_list = pcp_dict[year]
            array_list = []
            total_percentile_array = np.zeros(self.ref_array.shape)
            
            for f in annual_file_list:
                raster_array = self.raster.getRasterArray(f)
                array_list.append(raster_array)
            
            array_stack = np.stack((array_list))
            percentile_array = np.percentile(array_stack, self.percentile, axis=0, interpolation='higher')
            
            for f in annual_file_list:
                raster_array = self.raster.getRasterArray(f)
                if self.condition == 'higher':
                    condition_array = np.where(raster_array > percentile_array, raster_array, 0)
                elif self.condition == 'lower':
                    condition_array = np.where(raster_array < percentile_array, raster_array, 0)
                
                total_percentile_array = total_percentile_array + condition_array
            
            covariate_array = covariate_array + total_percentile_array 
            
        covariate_array = covariate_array / total_years
        covariate_array = np.where(self.ref_array == self.no_data, self.no_data, covariate_array)
        
        return covariate_array
    
class TotalPercentileRainfall20(TotalPercentileRainfall):
    
    percentile = 20
    condition = 'lower'


class ExtremeTempFreqPerMonth(ClimaticCovariates):
    
    '''
    A unique function to create climate layers of the frequency of days that the max daily temperature
    above or below extreme temperature within the interested month.
    
    start_date:       the start date of a certain period when the target covariate is matter
    end_date:         the end date of a certain period when the target covariate  is matter
    t1_key:           key words of temperature climate data subdir name (or filename)
    threshold_temp_1: the base temperature threshold of selected crop to calculate 
                      the target covariate         
    '''
    direction = ''
    
    def create_array(self, t1_key, start_date, end_date, threshold_temp_1):     

        
        t1_dict = self.__GetFileDictionary__(start_date, end_date, t1_key)
        
        array_list = []
#        i = 0
        for year in t1_dict:

                
            daily_array = np.zeros(self.ref_array.shape)
            accumu_daily_array = np.zeros(self.ref_array.shape)
            
            try:
                for f in t1_dict[year]:
                    raster_array = self.raster.getRasterArray(f)
                    if self.direction == 'below':
                        daily_array = np.where(raster_array < threshold_temp_1, 1, 0) 
                    elif self.direction == 'above':
                        daily_array = np.where(raster_array > threshold_temp_1, 1, 0) 
                    accumu_daily_array = accumu_daily_array + daily_array
            except:
                pass
            
            accumu_daily_array = np.where(self.ref_array == self.no_data, self.no_data, accumu_daily_array)
            array_list.append(accumu_daily_array)

        mean_array = np.mean(array_list, axis=0)
        mean_array = np.where(self.ref_array == self.no_data, self.no_data, mean_array)
        
        return mean_array
    
 
class HotTempFreqPerMonth(ExtremeTempFreqPerMonth):
    
    direction = 'above'   

class ColdTempFreqPerMonth(ExtremeTempFreqPerMonth):
    
    direction = 'below'       
    
class AccumulatedDailyTemperature(ClimaticCovariates):
    
    direction = ''
    flowering_accumu_temp = 0
    
    def create_array(self, t1_key, t2_key, start_date, end_date, threshold_temp_1, out_dir, crop_name, layer_name, ref_rst):     
        
        daily_dir = join(out_dir, 'daily')
        if not os.path.exists(daily_dir):
            os.makedirs(daily_dir, exist_ok = True)
        
        t1_dict = self.__GetFileDictionary__(start_date, end_date, t1_key)
        t2_dict = self.__GetFileDictionary__(start_date, end_date, t2_key)
        
        i = 0
        for year in t1_dict:
            if i == 0:
                start_year = year
                i+=1
            accumu_daily_array = np.zeros(self.ref_array.shape)
            
            annual_file_list_min = t1_dict[year]
            annual_file_list_max = t2_dict[year]
            accumu_daily_array = np.zeros(self.ref_array.shape)
            flowering_julian_day_array = np.zeros(self.ref_array.shape)
            
            for minf, maxf in zip(annual_file_list_min, annual_file_list_max):
                
                m = int(minf[:-4].split('-')[-2])
                d = int(minf[:-4].split('-')[-1])
                nth_day = get_nth_day(int(year), m, d)
                
                min_raster_array = self.raster.getRasterArray(minf)
                max_raster_array = self.raster.getRasterArray(maxf)
                    
                mean_raster_array = (min_raster_array + max_raster_array) / 2
                

                if self.direction == 'below':
                    daily_array = np.where(mean_raster_array < threshold_temp_1, mean_raster_array-threshold_temp_1, 0) 
                elif self.direction == 'above':
                    daily_array = np.where(mean_raster_array > threshold_temp_1, mean_raster_array-threshold_temp_1, 0) 
                
                accumu_daily_array = accumu_daily_array + daily_array
                accumu_daily_array = np.where(self.ref_array == self.no_data, self.no_data, accumu_daily_array)
                if np.amax(accumu_daily_array > 1000):
                    out_raster_file = join(daily_dir, '{}_{}_{}_{}.tif'.format(crop_name, layer_name, year, nth_day))
                    out_raster.array2Raster(accumu_daily_array, ref_rst, out_raster_file)

                flowering_julian_day_array = np.where(np.logical_and(accumu_daily_array > self.flowering_accumu_temp, flowering_julian_day_array == 0), nth_day, flowering_julian_day_array)
                
            flowering_julian_day_array = np.where(self.ref_array == self.no_data, self.no_data, flowering_julian_day_array)
            out_raster_julian = join(out_dir, '{}_{}_Flowering_Julian_{}.tif'.format(crop_name, layer_name, year))
            out_raster.array2Raster(flowering_julian_day_array, ref_rst, out_raster_julian)
            
        
        return None
    
class AccumulatedDailyTempHot(AccumulatedDailyTemperature):
    
    direction = 'above'
    flowering_accumu_temp = 1282
    

def get_nth_day(year, month, day):
    
    days_in_the_year = (dt.date(year, month, day)-dt.date(year, 1, 1)).days + 1
    
    return days_in_the_year


def getYearList(start_year, end_year):
    '''
    Return a year list based on the given start and end year
    '''
    year_list = []
    y = start_year
    while y <= end_year:
        year_list.append(str(y))
        y += 1
    return year_list

def generate(cov_id,     
             year_list, data_dir,  start_date,          end_date, 
             tmin_key,  tmax_key,  pcp_key,             threshold_temp_below,
             threshold_temp_above, threshold_pcp_above, threshold_pcp_below,
             out_dir,   crop_name, layer_name,          ref_rst):
    
    if cov_id in ['FFB','FFH']:
        array = AnnualFrostRiskFrequency(year_list, data_dir).create_array(tmin_key, start_date, end_date, threshold_temp_below)
        
    elif cov_id == 'GDD':   
        array = AnnualGDD(year_list, data_dir).create_array(tmin_key, tmax_key, start_date, end_date, threshold_temp_above)
    
    elif cov_id == 'CHL': 
        array = AnnualChillHours(year_list, data_dir).create_array(tmin_key, tmax_key, start_date, end_date, threshold_temp_above, threshold_temp_below)
    
    elif cov_id == 'MMM': 
        array = AnnualMeanMaxMonthlyBasedOnDaily(year_list, data_dir).create_array(tmax_key, start_date, end_date)
    
    elif cov_id in ['AMF', 'MXT']: 
        array = AnnualMeanDaily(year_list, data_dir).create_array(tmax_key, start_date, end_date)
        
    elif cov_id in ['MNT', 'MNS']: 
        array = AnnualMeanDaily(year_list, data_dir).create_array(tmin_key, start_date, end_date)
    
    elif cov_id == 'DMR': 
        array = AnnualMaxDailyTemperatureFrequency(year_list, data_dir).create_array(tmax_key, start_date, end_date, threshold_temp_above)
    
    elif cov_id == 'MIA':
        array = AnnualMinDailyTemperatureFrequencyAbove(year_list, data_dir).create_array(tmin_key, start_date, end_date, threshold_temp_above)
    
    elif cov_id == 'HFO':
        array = HeatStressFreq_Onion(year_list, data_dir).create_array(tmax_key, start_date, end_date, threshold_temp_above)
    
    elif cov_id == 'HFP':
        array = HeatStressFreq_Peas(year_list, data_dir).create_array(tmax_key, start_date, end_date, threshold_temp_above)
        
    elif cov_id == 'HFK':
        array = HeatStressFreq_Kumara(year_list, data_dir).create_array(tmax_key, start_date, end_date, threshold_temp_above)    
        
    elif cov_id == 'MET':
        array = MeanTemperature(year_list, data_dir).create_array(tmin_key, tmax_key, start_date, end_date)
        
    elif cov_id in ['ANR', 'RFS']:
        array = AnnualPCP(year_list, data_dir).create_array(pcp_key, start_date, end_date)
        
    elif cov_id == 'RAH':    
        array = PCPFreqHarvest(year_list, data_dir).create_array(pcp_key, start_date, end_date, threshold_pcp_above)
    
    elif cov_id in ['HTS','HTU','HTA','HTW']:
        array = DailyHighestTemperature(year_list, data_dir).create_array(tmax_key, start_date, end_date)
    
    elif cov_id == 'EMT':
        array = DailyLowestTemperature(year_list, data_dir).create_array(tmin_key, start_date, end_date)
    
    elif cov_id in ['LMS','LMU','LMA','LMW','LTS','LTO','LTN']:
        array = LowestMonthlyTemperature(year_list, data_dir).create_array(tmin_key, start_date, end_date)
    
    elif cov_id in ['LXS','LXO','LXN']:
        array = LowestMonthlyTemperature(year_list, data_dir).create_array(tmax_key, start_date, end_date)
    
    elif cov_id in ['LRS','LRU','LRA','LRW']:
        array = TotalPercentileRainfall20(year_list, data_dir).create_array(pcp_key, start_date, end_date)
        
    elif cov_id == 'FRD':
        array = ColdTempFreqPerMonth(year_list, data_dir).create_array(tmax_key, start_date, end_date, threshold_temp_below)
        
    elif cov_id == 'HOD': 
        array = HotTempFreqPerMonth(year_list, data_dir).create_array(tmax_key, start_date, end_date, threshold_temp_above)
#    
#    elif cov_id == 'ACT': 
#        array = AccumulatedDailyTempHot(year_list, data_dir).create_array(tmin_key, tmax_key, start_date, end_date, threshold_temp_above, out_dir, crop_name, layer_name, ref_rst)
    else:
        return None
    
    return array


        
        
        