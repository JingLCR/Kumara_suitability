# -*- coding: utf-8 -*-
"""
Created on Thu Mar 22 10:10:09 2018

@author: guoj

This script is for SLMACC project. It is the second step of land suitability mapping.
It homogenizes, including resolution, extend and projection, all the covariate layers.

"""


import os
from os.path import join
from os import walk
import shutil
import datetime as dt

from config import ConfigParameters
from raster import Raster
from sqlite_conn import Sqlite_connection
from geoprocessing_2022 import GeoProcessing
import climate_covariate as cc
import rasterio
from rasterio.fill import fillnodata

import fiona
import geopandas as gpd
import pandas as pd
import numpy.ma as ma

def strip_end(text, suffix):
    if not text.endswith(suffix):
        return text
    return text[:len(text)-len(suffix)]

def strip_start(text, suffix):
    if not text.startswith(suffix):
        return text
    return text[len(suffix):]

       

class CovariateGenerator(GeoProcessing):
    
    def __init__(self, db_conn, no_data):
        self.no_data = no_data
        self.conn = db_conn
        self.ref_raster = ''
    
    def set_ref_raster(self, ref_rst):
        self.ref_raster = ref_rst
    
    def set_ref_raster_dir(self, data_dir):
        for (subdirpath, subdirname, filenames) in walk(data_dir):
            for f in filenames:
                if f.split('.')[-1].lower()[:3] == 'tif':
                    self.ref_raster = join(subdirpath, f)
    
    def create_soil_covariates(self, soil_file, spat_res, out_dir):
        if not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok = True)
        
        with self.conn as cur:
            rows = cur.execute("select * from Covariate where category=?", ('soil',)).fetchall()
        
        if rows:
            print('Start to generate soil covariates...')
            for row in rows:
                cova_id = row['id']

                cova = row['covariate'] # for printing
                attr = row['shp_attr']
                print('Generate {} at {} ...'.format(cova, dt.datetime.now()))
                self.ESRIVector2Raster(soil_file, cova_id, attr, spat_res, out_dir)
                
    def create_multisoil_covariates(self, soil_data, spat_res, out_dir, driver='GPKG'):
    
        if driver not in ['GPKG', 'FileGDB']:
            print ('Error! Soil data format must be GPKG or GDB!')
            return
    
        rst = Raster()
                
        
        with self.conn as cur:
            rows = cur.execute("select * from Covariate where category=?", ('soil',)).fetchall()
        
        if rows:
            print('Start to generate soil covariates...')
            
            smap_layers = fiona.listlayers(soil_data)
            
            for l in smap_layers:
                gdf = gpd.read_file(soil_data, driver=driver, layer=l)
                vector_id = gdf['Smap_ObjectID'].tolist()
                
                unconverted_id = vector_id
                # soil_l = l
                
                i = 0
                
                new_soil_l = l
                
                while len(unconverted_id) > 0:
                    
                    out_d = join(out_dir, 'round{}'.format(i), l)
                    if not os.path.exists(out_d):
                        os.makedirs(out_d, exist_ok = True)
                        
                    soil_l = new_soil_l
                    
                    print('# of unconverted items: {}'.format(len(unconverted_id)))
                    
                    for row in rows:
                        cova_id = row['id']
        
                        cova = row['covariate'] # for printing
                        attr = row['shp_attr']
                        print('Generate {} at {} ...'.format(cova, dt.datetime.now()))
                        
                        soil_file = join(soil_data, soil_l)
                    
                        soil_raster = self.Vector2Raster(soil_file, cova_id, attr, spat_res, out_d)
                        
                        
                        if cova_id == 'OID':
                            rst_array = rst.getRasterArray(soil_raster)
                            raster_id = ma.masked_invalid(rst_array).flatten().tolist() 
                            
                            unconverted_id = list(set(vector_id) - set(raster_id))
                        
                            if len(unconverted_id) > 0:
                                
                                mask = gdf['Smap_ObjectID'].isin(unconverted_id)
                                gdf_small = gdf.loc[mask]
                                new_soil_l = 'smallploy_round{}_{}'.format(i+1,l)
                                gdf_small.to_file(soil_data, layer=new_soil_l, driver=driver)
                                
                                vector_id = unconverted_id
                                
                                i += 1
                    
                    
                    
    
    def create_terrain_covariates(self, terrain_file, out_dir, terrain_id):
        if not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok = True)
            
        with self.conn as cur:
            rows = cur.execute("select * from Covariate where category=?", ('terrain',)).fetchall()
        
        if rows:
            for row in rows:
                if row['id'] == terrain_id:
                    print('Start to generate terrain covariates...')
                    cova_id = row['id']
                    cova = row['covariate']
                    print('Generate {} at {} ...'.format(cova, dt.datetime.now()))
                    new_filename = join(out_dir, '{}.tif'.format(cova_id))
                    shutil.copy(terrain_file, new_filename)
    
    def create_climate_covariates(self, climate_dir, start_year, end_year, key_min, key_max, key_pcp, out_dir):
        abstemp = 273.15
        
        year_list = cc.getYearList(start_year, end_year)    
        climate_covariate = cc.ClimaticCovariates(year_list, climate_dir)
        ref_raster = climate_covariate.ref_raster
        
        out_raster = Raster()
        
        crops_id = []
        crops = []
        
        with self.conn as cur:
            rows = cur.execute("select * from crop").fetchall()
        
        if rows:
            print('Start to generate climate covariates...')
            for row in rows:
                crops_id.append(row['id'])
                crops.append(row['crop'])
            
            
            for crop_id, crop in zip(crops_id, crops):
                
                if crop_id != 'KM':
                    continue
        
                print(crop)
                with self.conn as cur:
                    covariates = cur.execute("select * from covariate_threshold where crop_id=?", (crop_id,)).fetchall()
        
                if covariates:
                    for covariate in covariates:
                        with self.conn as cur:
                            covariate_name = cur.execute("select covariate from Covariate where id=?", (covariate['covariate_id'],)).fetchone()['covariate']
                        print('Generate {} at {} ...'.format(covariate_name, dt.datetime.now()))
                        
                        if covariate['t_below'] is not None:
                            try:
                                t_below = float(covariate['t_below']) + abstemp
                            except ValueError:
                                t_below = None
                        else:
                            t_below = None
                        
                        if covariate['t_above'] is not None:
                            try:
                                t_above = float(covariate['t_above']) + abstemp
                            except ValueError:
                                t_above = None
                        else:
                            t_above = None
                            
                        if covariate['pcp_above'] is not None:
                            try:
                                pcp_above = float(covariate['pcp_above'])
                            except ValueError:
                                pcp_above = None
                        else:
                            pcp_above = None
                            
                        if covariate['pcp_below'] is not None:
                            try:
                                pcp_below = float(covariate['pcp_below'])
                            except ValueError:
                                pcp_below = None
                        else:
                            pcp_below = None
                            
# =============================================================================
#                         out_sub_dir = join(out_dir, crop)
#                         if not os.path.exists(out_sub_dir):
#                             os.makedirs(out_sub_dir, exist_ok = True)
# =============================================================================
                                    
                        covariate_array = cc.generate(covariate['covariate_id'], year_list, 
                                                      climate_dir,               covariate['start_date'],
                                                      covariate['end_date'],     key_min,
                                                      key_max,                   key_pcp,
                                                      t_below,                   t_above,
                                                      pcp_above,                 pcp_below,
                                                      out_dir,               crop_id,
                                                      covariate['covariate_id'], ref_raster)
        
                        try:
                            if covariate_array is not None:    
                                
                                out_raster_file = join(out_dir, '{}_{}_{}_{}.tif'.format(crop_id, covariate['covariate_id'], start_year, end_year))
                                out_raster.array2Raster(covariate_array, ref_raster, out_raster_file)
                        except:
                            pass
    
    def covariate_interpolate(self, in_dir, out_dir):
        
        # out_dir = join(out_dir,'Kumara')
        # if not os.path.exists(out_dir):
        #     os.makedirs(out_dir, exist_ok = True)
        
        for (subdirpath, subdirname, filenames) in walk(in_dir):
                for f in filenames:
                    if f.split('.')[-1].lower()[:3] == 'tif':
                        tif_file = join(subdirpath, f)
                        with rasterio.open(tif_file) as src:
                            profile = src.profile
                            arr = src.read(1)
                            arr_filled = fillnodata(arr, mask=src.read_masks(1), max_search_distance=5, smoothing_iterations=0)
                        
                        newtif_file = join(out_dir, f)  
                        with rasterio.open(newtif_file, 'w', **profile) as dest:
                            dest.write_band(1, arr_filled)
            
    
    def covariate_processing(self, dir_list, out_dir):
        
        for in_dir in dir_list:
            for (subdirpath, subdirname, filenames) in walk(in_dir):
                for f in filenames:
                    if f.split('.')[-1].lower()[:3] == 'tif':
                        
                        sub_out_dir = join(out_dir, strip_start(subdirpath, in_dir)[1:])
                        
                        if not os.path.exists(sub_out_dir):
                            os.makedirs(sub_out_dir, exist_ok = True)
                        
                        outrst = join(sub_out_dir, f)
                        
# =============================================================================
#                         if in_dir == dir_list[0]:
# #                            pass
#                             self.reproject_raster(join(subdirpath, f), self.ref_raster, outrst)    
#                         else:
#                             self.reproject_raster2(join(subdirpath, f), self.ref_raster, outrst)    
# =============================================================================
                        
                        self.reproject_raster_3(join(subdirpath, f), outrst, self.ref_raster)
    
    
# =============================================================================
# def main():
#     
#     conf = input('Please enter the full dir and filename of config file\n(Enter): ')
#     
#     while not os.path.isfile(conf):
#         print('The config.ini file does not exist. Would you like to use the default file?')
#         is_default = input('(Yes/No): ')
#         if is_default[0].lower() == 'y': 
#             conf = r'config.ini'
#         else:
#             conf = input('Please enter the full dir and filename of config file.\nOr leave it blank to point to the default file\n (Enter): ')
#     
#     config_params = ConfigParameters(conf)
#     proj_header = 'projectConfig'
#     cli_header = 'climateIndices'
#     prep_header = 'preprocessing'
#     
#     db_file = config_params.GetDB(proj_header)
#     
#     #    out_raster = Raster()
#     
#     conn = Sqlite_connection(db_file)
# 
#     cova = CovariateGenerator(conn, -9999)
#     
#     
#     # 1. Create soil and terrain covariates
#     soil_cova_dir = config_params.GetSoilCovariateDir(proj_header)
#     terr_cova_dir = config_params.GetTerrainCovariateDir(proj_header)
#     soil_file, slope_file, ph_file, luc_file, spat_res = config_params.GetPreprocessingParams(proj_header, prep_header)
#     
#     # cova.create_soil_covariates(soil_file, spat_res, soil_cova_dir)   
#     cova.create_multisoil_covariates(soil_file, spat_res, soil_cova_dir)  
#     
#     
#     
# # =============================================================================
# #     cova.create_terrain_covariates(slope_file, terr_cova_dir, 'SLP')
# #     cova.create_terrain_covariates(ph_file, terr_cova_dir, 'PHH')
# # =============================================================================
#     
#     # 2. Create climate covariates
# # =============================================================================
# #     cli_cova_dir = config_params.GetClimateCovariateDir(proj_header)
# #     climate_dir, start_year, end_year, key_min, key_max, key_pcp = config_params.GetClimateCovariateParams(proj_header, cli_header)
# # =============================================================================
# #    cli_scenario = config_params.GetClimateScenario(proj_header)
#     
#     # this is the climate data source directory. If use other climate scenario just change the era to other rcp plus climate model
# #    climate_dir = join(climate_dir, 'vcsn')
#     
#     # This is the output directory of created climate covariates. It will also be used by the suitability mapping app.
# #    covariate_sub_dir = join(cli_cova_dir, cli_scenario['era'])
# 
# # =============================================================================
# #     cova.create_climate_covariates(climate_dir, start_year, end_year, key_min, key_max, key_pcp, cli_cova_dir) 
# #     
# #     # interpolate climate date to match the soil data coverage. the cli_cova_interpolate_dir isn't correctly set. Future correction needed. 
# #     cli_cova_interpolate_dir = join(cli_cova_dir, 'interpolate')    
# #     if not os.path.exists(cli_cova_interpolate_dir):
# #         os.makedirs(cli_cova_interpolate_dir, exist_ok = True)
# #         
# #     cova.covariate_interpolate(cli_cova_dir, cli_cova_interpolate_dir)
# #     
# #     # 3. covariates processing, including reprojection and resampling
# #     # using one of the soil covariate layer as a reference raster
# #         
# #     target_dirs = [terr_cova_dir, cli_cova_interpolate_dir]
# # =============================================================================
# #    target_dirs = [cli_cova_dir]
# # =============================================================================
# #     Procd_cova_dir = config_params.GetProcessedCovariateDir(proj_header)    
# #     if not os.path.exists(Procd_cova_dir):
# #         os.makedirs(Procd_cova_dir, exist_ok = True)
# #     
# #     # frist copy all the soil covariate layers directly to the new dir, they dont need to be processed    
# #     for (subdirpath, subdirname, filenames) in walk(soil_cova_dir):
# #         for f in filenames:
# #             if f.split('.')[-1].lower()[:3] == 'tif':
# #                 new_filename = join(Procd_cova_dir, f)
# #                 shutil.copy(join(subdirpath, f), new_filename)    
# # =============================================================================
#     
# # =============================================================================
# #     # second, deal with the rest    
# #     # cova.set_ref_raster_dir(soil_cova_dir)
# #     cova.set_ref_raster(r'C:\Users\guoj\projects\682002-0037 PFR 1 Landuse Suitability\kumara\covariate_20210825_sib1\soil')
# #     cova.covariate_processing(target_dirs, Procd_cova_dir)
# # =============================================================================
# 
#     print('Finished at {} ...'.format(dt.datetime.now()))
#     
#     
# if __name__ == '__main__':
#     main()    
# =============================================================================
    
