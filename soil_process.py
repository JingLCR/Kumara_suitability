# -*- coding: utf-8 -*-
"""
Created on T Fri Sep 30 10:55:41 2022

@author: guoj

Rasterize soil data from SMap. 
"""

from covariate_preprocessing_v3 import CovariateGenerator as CG
import os
import datetime as dt

from config import ConfigParameters
from sqlite_conn import Sqlite_connection


def main():
    
    conf = input('Please enter the full dir and filename of config file\n(Enter): ')
    
    while not os.path.isfile(conf):
        print('The config.ini file does not exist. Would you like to use the default file?')
        is_default = input('(Yes/No): ')
        if is_default[0].lower() == 'y': 
            conf = r'config.ini'
        else:
            conf = input('Please enter the full dir and filename of config file.\nOr leave it blank to point to the default file\n (Enter): ')
    
    config_params = ConfigParameters(conf)
    proj_header = 'projectConfig'
    prep_header = 'preprocessing'
    
    db_file = config_params.GetDB(proj_header)
    
    conn = Sqlite_connection(db_file)

    cova = CG(conn, -9999)
    
    # Create soil covariates from SMap
    soil_cova_dir = config_params.GetSoilCovariateDir(proj_header)
    soil_file, slope_file, ph_file, luc_file, spat_res = config_params.GetPreprocessingParams(proj_header, prep_header)
    
    # cova.create_soil_covariates(soil_file, spat_res, soil_cova_dir) # Use this function when only one sibling layer needs to be rasterized and small polygon issue can be ignored
    cova.create_multisoil_covariates(soil_file, spat_res, soil_cova_dir)  

    print('Finished at {} ...'.format(dt.datetime.now()))
    
    
if __name__ == '__main__':
    main()    