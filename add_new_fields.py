# -*- coding: utf-8 -*-
"""
Created on Tue Aug 24 10:38:55 2021

@author: GuoJ
"""

import fiona
import geopandas as gpd
import pandas as pd
from os.path import join
import os

def Texture(x):
    return {
        'Clayey':1,
        'Loamy':2,
        'Peaty':3,
        'Sandy':4,
        'Silty':5,
        }.get(x, 6)

def Material(x):
    return {
        'Ma':1,
        'Md':2,
        'Mf':3,
        'Mg':4,
        'Ml':5,
        'Mm':6,
        'Mp':7,
        'Mr':8,
        'Ms':9,
        'Mt':10,
        'Sd':11,
        'Sl':12,
        'So':13,
        'Sp':14,
        }.get(x, 15)

def Hydrology(x):
    if 'A' in x:
        return 1
    elif 'B' in x and 'A' not in x:
        return 2
    elif 'C' in x and 'A' not in x and 'B' not in x:
        return 3
    elif 'D' in x and 'A' not in x and 'B' not in x and 'C' not in x:
        return 4
    else:
        return 5


def Order(x):
    return {
        'A':1,
        'B':2,
        'E':3,
        'G':4,
        'L':5,
        'M':6,
        'N':7,
        'O':8,
        'P':9,
        'R':10,
        'S':11,
        'U':12,
        'W':13,
        'X':14,
        'Z':15,
        }.get(x, 0)


def Salinity(x):
    return {
        'S':1,
        'M':2,
        'W':3,
        'N':4,
        }.get(x, 0)

def convertDepth(depthMean):
    
    def remove_chars_iter(subj, chars):
        sc = set(chars)
        return ''.join([c for c in subj if c not in sc])
        
    inText = depthMean
    remove_list = ['>', '<', '=', ' ', 'c', 'm']
    
    sdp_mean = remove_chars_iter(inText, remove_list)
    
    sdp_mean = float(sdp_mean)
    
    return sdp_mean

def getDrainageCode(x):
    return {
        'vp':1,
        'p':2,
        'i':3,
        'mw':4,
        'w':5,
        }.get(x, 0)

def getNZSCCode(x):
    return {
		"AFST":1,   "BOC":31,  "GAO":61,  "LOV":91,   "PJMU":121, "RHI":151,  "UYZ":181,  "LGO":211,
		"AM":2,     "BOH":32,  "GAT":62,  "LPT":92,   "PJMW":122, "ROA":152,  "WF":182,   "NOL":212,
		"ATT":3,    "BOI":33,  "GAY":63,  "MIM":93,   "PJN":123,  "ROM":153,  "WGF":183,  "RXA":213,
		"ATX":4,    "BOM":34,  "GOA":64,  "MIW":94,   "PJT":124,  "ROT":154,  "WGFQ":184, "UDP":214,
		"BAM":5,    "BOMA":35, "GOC":65,  "MOBL":95,  "PJU":125,  "ROW":155,  "WGQ":185,  "UYBG":215,
		"BAMP":6,   "BOP":36,  "GOE":66,  "MOI":96,   "PJW":126,  "RSA":156,  "WGT":186,  "ZDYH":216,
		"BAO":7,    "BOT":37,  "GOI":67,  "MOL":97,   "PLM":127,  "RSM":157,  "WHA":187,  "ZDQ":217,
		"BAP":8,    "BOW":38,  "GOJ":68,  "MOM":98,   "PLT":128,  "RST":158,  "WO":188,   "PPWJ":218,
		"BAT":9,    "BSA":39,  "GOO":69,  "MOT":99,   "PPC":129,  "RTBP":159, "WS":189,
		"BFA":10,   "BSM":40,  "GOQ":70,  "MOZ":100,  "PPJ":130,  "RTM":160,  "WT":190,
		"BFAL":11,  "BSMP":41, "GOT":71,  "MPT":101,  "PPJX":131, "RTT":161,  "WW":191,
		"BFC":12,   "BSP":42,  "GRA":72,  "NOM":102,  "PPT":132,  "RXT":162,  "WX":192,
		"BFL":13,   "BST":43,  "GRF":73,  "NOT":103,  "PPU":133,  "SAH":163,  "ZDH":193,
		"BFM":14,   "BXT":44,  "GRO":74,  "NPT":104,  "PPX":134,  "SAM":164,  "ZOH":194,
		"BFMA":15,  "EMM":45,  "GRQ":75,  "NXT":105,  "PUJ":135,  "SAT":165,  "ZOT":195,
		"BFMP":16,  "EMT":46,  "GRT":76,  "OFA":106,  "PUM":136,  "SAW":166,  "ZPH":196,
		"BFP":17,   "EOC":47,  "GSA":77,  "OFM":107,  "PUT":137,  "SIM":167,  "ZPHP":197,
		"BFT":18,   "EODC":48, "GSC":78,  "OFS":108,  "PXJ":138,  "SIT":168,  "ZPOZ":198,
		"BFW":19,   "EOJ":49,  "GSO":79,  "OHA":109,  "PXJN":139, "SJK":169,  "ZPP":199,
		"BLA":20,   "EOJC":50, "GSQ":80,  "OHM":110,  "PXM":140,  "SJL":170,  "ZPQ":200,
		"BLAD":21,  "EOM":51,  "GST":81,  "OMA":111,  "PXMJ":141, "SJM":171,  "ZPT":201,
		"BLAM":22,  "EOMC":52, "GTO":82,  "OMM":112,  "PXT":142,  "SJQ":172,  "ZPU":202,
		"BLD":23,   "EOMJ":53, "GTT":83,  "PIC":113,  "RFA":143,  "SJT":173,  "ZPZ":203,
		"BLF":24,   "EOT":54,  "GUFQ":84, "PID":114,  "RFAW":144, "SZQ":174,  "ZXF":204,
		"BLM":25,   "ERT":55,  "GUT":85,  "PIM":115,  "RFM":145,  "UDM":175,  "ZXH":205,
		"BLT":26,   "ERW":56,  "LIM":86,  "PIMD":116, "RFMA":146, "UEM":176,  "ZXP":206,
		"BMA":27,   "EVM":57,  "LIT":87,  "PIT":117,  "RFMQ":147, "UEP":177,  "ZXQ":207,
		"BMM":28,   "EVMC":58, "LOA":88,  "PJA":118,  "RFMW":148, "UPT":178,  "ZXU":208,
		"BMT":29,   "EVT":59,  "LOM":89,  "PJC":119,  "RFT":149,  "UYM":179,  "BOMW":209,
		"BOA":30,   "GAH":60,  "LOT":90,  "PJM":120,  "RFW":150,  "UYT":180,  "EPJ":210,
		}.get(x,0)


def main():
    
    
    drainage_mapping = {
                        'vp':1,
                        'p':2,
                        'i':3,
                        'mw':4,
                        'w':5
                        }
    
    texture_mapping = {
                        'Clayey':1,
                        'Loamy':2,
                        'Peaty':3,
                        'Sandy':4,
                        'Silty':5
                        }
    
    
    
    
    matierial_mapping = {
                        'Ma':1,
                        'Md':2,
                        'Mf':3,
                        'Mg':4,
                        'Ml':5,
                        'Mm':6,
                        'Mp':7,
                        'Mr':8,
                        'Ms':9,
                        'Mt':10,
                        'Sd':11,
                        'Sl':12,
                        'So':13,
                        'Sp':14
                        }
    
    order_mapping = {
                    'A':1,
                    'B':2,
                    'E':3,
                    'G':4,
                    'L':5,
                    'M':6,
                    'N':7,
                    'O':8,
                    'P':9,
                    'R':10,
                    'S':11,
                    'U':12,
                    'W':13,
                    'X':14,
                    'Z':15
                    }
    
    salinity_mapping = {
                        'S':1,
                        'M':2,
                        'W':3,
                        'N':4
                        }
    
    soildepth_mapping = [r'>', r'<', r'=', r' ', r'c', r'm']
    
    nzsc_mapping = {
		"AFST":1,   "BOC":31,  "GAO":61,  "LOV":91,   "PJMU":121, "RHI":151,  "UYZ":181,  "LGO":211,
		"AM":2,     "BOH":32,  "GAT":62,  "LPT":92,   "PJMW":122, "ROA":152,  "WF":182,   "NOL":212,
		"ATT":3,    "BOI":33,  "GAY":63,  "MIM":93,   "PJN":123,  "ROM":153,  "WGF":183,  "RXA":213,
		"ATX":4,    "BOM":34,  "GOA":64,  "MIW":94,   "PJT":124,  "ROT":154,  "WGFQ":184, "UDP":214,
		"BAM":5,    "BOMA":35, "GOC":65,  "MOBL":95,  "PJU":125,  "ROW":155,  "WGQ":185,  "UYBG":215,
		"BAMP":6,   "BOP":36,  "GOE":66,  "MOI":96,   "PJW":126,  "RSA":156,  "WGT":186,  "ZDYH":216,
		"BAO":7,    "BOT":37,  "GOI":67,  "MOL":97,   "PLM":127,  "RSM":157,  "WHA":187,  "ZDQ":217,
		"BAP":8,    "BOW":38,  "GOJ":68,  "MOM":98,   "PLT":128,  "RST":158,  "WO":188,   "PPWJ":218,
		"BAT":9,    "BSA":39,  "GOO":69,  "MOT":99,   "PPC":129,  "RTBP":159, "WS":189,
		"BFA":10,   "BSM":40,  "GOQ":70,  "MOZ":100,  "PPJ":130,  "RTM":160,  "WT":190,
		"BFAL":11,  "BSMP":41, "GOT":71,  "MPT":101,  "PPJX":131, "RTT":161,  "WW":191,
		"BFC":12,   "BSP":42,  "GRA":72,  "NOM":102,  "PPT":132,  "RXT":162,  "WX":192,
		"BFL":13,   "BST":43,  "GRF":73,  "NOT":103,  "PPU":133,  "SAH":163,  "ZDH":193,
		"BFM":14,   "BXT":44,  "GRO":74,  "NPT":104,  "PPX":134,  "SAM":164,  "ZOH":194,
		"BFMA":15,  "EMM":45,  "GRQ":75,  "NXT":105,  "PUJ":135,  "SAT":165,  "ZOT":195,
		"BFMP":16,  "EMT":46,  "GRT":76,  "OFA":106,  "PUM":136,  "SAW":166,  "ZPH":196,
		"BFP":17,   "EOC":47,  "GSA":77,  "OFM":107,  "PUT":137,  "SIM":167,  "ZPHP":197,
		"BFT":18,   "EODC":48, "GSC":78,  "OFS":108,  "PXJ":138,  "SIT":168,  "ZPOZ":198,
		"BFW":19,   "EOJ":49,  "GSO":79,  "OHA":109,  "PXJN":139, "SJK":169,  "ZPP":199,
		"BLA":20,   "EOJC":50, "GSQ":80,  "OHM":110,  "PXM":140,  "SJL":170,  "ZPQ":200,
		"BLAD":21,  "EOM":51,  "GST":81,  "OMA":111,  "PXMJ":141, "SJM":171,  "ZPT":201,
		"BLAM":22,  "EOMC":52, "GTO":82,  "OMM":112,  "PXT":142,  "SJQ":172,  "ZPU":202,
		"BLD":23,   "EOMJ":53, "GTT":83,  "PIC":113,  "RFA":143,  "SJT":173,  "ZPZ":203,
		"BLF":24,   "EOT":54,  "GUFQ":84, "PID":114,  "RFAW":144, "SZQ":174,  "ZXF":204,
		"BLM":25,   "ERT":55,  "GUT":85,  "PIM":115,  "RFM":145,  "UDM":175,  "ZXH":205,
		"BLT":26,   "ERW":56,  "LIM":86,  "PIMD":116, "RFMA":146, "UEM":176,  "ZXP":206,
		"BMA":27,   "EVM":57,  "LIT":87,  "PIT":117,  "RFMQ":147, "UEP":177,  "ZXQ":207,
		"BMM":28,   "EVMC":58, "LOA":88,  "PJA":118,  "RFMW":148, "UPT":178,  "ZXU":208,
		"BMT":29,   "EVT":59,  "LOM":89,  "PJC":119,  "RFT":149,  "UYM":179,  "BOMW":209,
		"BOA":30,   "GAH":60,  "LOT":90,  "PJM":120,  "RFW":150,  "UYT":180,  "EPJ":210,
		}
    
    
    
    
    workspace = r'C:\Users\guoj\projects\FY22-23\Kumara_suitability\data\smap'
    smap_gdb = join(workspace, r'SmapKumara20220922.gdb')
    out_dir = join(workspace, 'SmapKumara20220922.gpkg')
    
    # if not os.path.exists(out_dir):
    #     os.makedirs(out_dir, exist_ok = True)
    
# =============================================================================
#     out_dir = join(workspace, r'SmapKumara20210825')
#     out_dir_small = join(workspace, r'SmapKumara20210825small')
#    
#     oid_csv = r'C:\Users\guoj\projects\682002-0037 PFR 1 Landuse Suitability\kumara\not_working_oid.csv'
#     df_oid = pd.read_csv(oid_csv)
#     oid_list = df_oid['not_working_oid'].tolist() 
# =============================================================================
   
    smap_layers = fiona.listlayers(smap_gdb)
    for l in smap_layers:
        
        print(l)
        gdf = gpd.read_file(smap_gdb, driver='FileGDB', layer=l)
        
        gdf['DRAIN_CLS'] = gdf['SiblingDrainageCode'].replace(drainage_mapping)
        gdf['NZSC_CLS'] = gdf['NZSC'].replace(nzsc_mapping)
        gdf['SDP_MEAN'] = gdf['DepthMean'].replace(regex=soildepth_mapping, value='').astype('float32')
        gdf.to_file(out_dir, layer=l, driver='GPKG')
        
# =============================================================================
#         mask = gdf['OBJECTID'].isin(oid_list)
#         gdf_small = gdf.loc[mask]
#         gdf_small.to_file(out_dir_small, layer=l)
# =============================================================================
        
if __name__ == '__main__':
    main()