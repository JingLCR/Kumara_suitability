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

from config import ConfigParameters
from sqlite_conn import Sqlite_connection


def main():
    
    conf = r'config.ini'
    
    config_params = ConfigParameters(conf)
    proj_header = 'projectConfig'
    prep_header = 'preprocessing'
    
    db_file = config_params.GetDB(proj_header)
    
    #    out_raster = Raster()
    
    conn = Sqlite_connection(db_file)

    cova = CG(conn, -9999)
    
    
    # 1. Create terrain covariates
    terr_cova_dir = config_params.GetTerrainCovariateDir(proj_header)
    soil_file, slope_file, ph_file, luc_file, spat_res = config_params.GetPreprocessingParams(proj_header, prep_header)
    
    print('Would you like to only resample the data?')
    is_default = input('(Yes/No): ')
    if is_default[0].lower() == 'y': 
        pass
    else:
        cova.create_terrain_covariates(slope_file, terr_cova_dir, 'SLP')
        cova.create_terrain_covariates(ph_file, terr_cova_dir, 'PHH')
    
        
    # covariates processing, including reprojection and resampling
    # using one of the soil covariate layer as a reference raster, soil layers don't need to be processed
        
# =============================================================================
    target_dirs = [terr_cova_dir]
    Procd_cova_dir = config_params.GetProcessedCovariateDir(proj_header)    
    
    # Iterate soil layer dir (processed dir), terrain layers need to be processed according to each soil dir.    
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
    
    
    
    
    
    
    
    
    
    
    