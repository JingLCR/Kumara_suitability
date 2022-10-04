# -*- coding: utf-8 -*-
"""
Created on Fri Sep 30 12:30:13 2022

@author: GuoJ
"""

# -*- coding: utf-8 -*-
"""
Created on T Fri Sep 30 10:55:41 2022

@author: guoj

Process terrain and PH data. 
"""
from os.path import join
from os import walk
from covariate_preprocessing_v3 import CovariateGenerator as CG
import datetime as dt
import os
from config import ConfigParameters
from sqlite_conn import Sqlite_connection


def main():
    
    conf = r'config.ini'
    
    config_params = ConfigParameters(conf)
    proj_header = 'projectConfig'
    cli_header = 'climateIndices'
    
    db_file = config_params.GetDB(proj_header)
    
    #    out_raster = Raster()
    
    conn = Sqlite_connection(db_file)

    cova = CG(conn, -9999)
    
    
    # Create climate covariates
    climate_dir, start_year, end_year, key_min, key_max, key_pcp = config_params.GetClimateCovariateParams(proj_header, cli_header)
    cli_cova_dir = config_params.GetClimateCovariateDir(proj_header)
    cli_cova_interpolate_dir = join(cli_cova_dir, 'interpolate')
    
    # Create climate covariates from daily climate data
    print('Would you like to only resample the data?')
    is_default = input('(Yes/No): ')
    if is_default[0].lower() == 'y': 
        # target_dirs = [cli_cova_dir]
        target_dirs = [cli_cova_interpolate_dir]
    else:
        print('Do you want to interpolate data?')
        is_default = input('(Yes/No): ')
        
        if is_default[0].lower() == 'y': 
        
            cova.create_climate_covariates(climate_dir, start_year, end_year, key_min, key_max, key_pcp, cli_cova_dir) 
            
            # interpolate climate date to match the soil data coverage. the cli_cova_interpolate_dir isn't correctly set. Future correction needed. 
            if not os.path.exists(cli_cova_interpolate_dir):
                os.makedirs(cli_cova_interpolate_dir, exist_ok = True)
                
            cova.covariate_interpolate(cli_cova_dir, cli_cova_interpolate_dir)
            target_dirs = [cli_cova_interpolate_dir]
        
        else: 
            cova.create_climate_covariates(climate_dir, start_year, end_year, key_min, key_max, key_pcp, cli_cova_dir) 
            target_dirs = [cli_cova_dir]
    
        
    # covariates processing, including reprojection and resampling
    # using one of the soil covariate layer as a reference raster, soil layers don't need to be processed
        
    target_dirs = [cli_cova_interpolate_dir]
    Procd_cova_dir = config_params.GetProcessedCovariateDir(proj_header)    
    
    # Iterate soil layer dir (processed dir), climate layers need to be processed according to each soil dir.    
    for (subdirpath, subdirname, filenames) in walk(Procd_cova_dir):
        for f in filenames:
            if f == 'OID.tif':
                print(subdirpath)
                cova.set_ref_raster(join(subdirpath, f))
                cova.covariate_processing(target_dirs, subdirpath)
          
                continue
          
            
          
            

    print('Finished at {} ...'.format(dt.datetime.now()))
    
    
if __name__ == '__main__':
    main()    
    
    
    
    
    
    
    
    
    
    
    