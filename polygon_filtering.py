# -*- coding: utf-8 -*-
"""
Created on Fri Aug 20 13:31:38 2021

@author: GuoJ
"""

import fiona
import geopandas as gpd
import pandas as pd
from os.path import join

def main():
    
    workspace = r'C:\Users\guoj\projects\682002-0037 PFR 1 Landuse Suitability\kumara'
    #smap_gdb = r'C:\Users\guoj\projects\682002-0037 PFR 1 Landuse Suitability\data\soil\Smap Kumara data 20210802.gdb'
    smap_dir = r'C:\Users\guoj\projects\682002-0037 PFR 1 Landuse Suitability\data\soil\SmapKumara20210825small_2round'
    oid_csv = join(workspace, r'not_working_oid_3round.csv')
    
    out_dir = r'C:\Users\guoj\projects\682002-0037 PFR 1 Landuse Suitability\data\soil\SmapKumara20210825small_3round'
    df_oid = pd.read_csv(oid_csv)
    oid_list = df_oid['not_working_oid'].tolist()
    
    # smap_layers = fiona.listlayers(smap_gdb)
    smap_layers = ['KumaraData_Sib{}'.format(x) for x in range(1, 6)]
    for l in smap_layers:
        
        print(l)
        gdf = gpd.read_file(join(smap_dir, '{}.shp'.format(l)), driver='Shapefile')
        
        mask = gdf['OBJECTID'].isin(oid_list)
        gdf = gdf.loc[mask]
        
        if len(gdf) > 0:
            gdf.to_file(out_dir, layer=l)

if __name__ == '__main__':
    main()