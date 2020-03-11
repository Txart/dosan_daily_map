# -*- coding: utf-8 -*-
"""
Created on Tue Mar  3 15:00:29 2020

@author: 03125327
"""
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
import sys
import pickle
import os
if sys.version_info[0] < 3:  # Fork for python2 and python3 compatibility
    from StringIO import StringIO
else:
    from io import StringIO

import preprocess_data,  utilities, hydro, hydro_utils, read

"""
FUNCTIONS
"""
def get_instantaneous_weather_data():
    DID =  '001D0A00F65E' # DEVIDE ID
    password = 'putri061112'
    apiToken = 'CF4BCA6F352A46358FAF00E7E9009516'
    api_url = 'https://api.weatherlink.com/v1/NoaaExt.json?user=' + DID + '&pass=' + password + '&apiToken=' + apiToken

    
    # This is where the request happens
    response = requests.request(method='POST', url=api_url)
    print('HTTP response status code: ', response.status_code)
    data = response.content.decode('utf-8')
    return pd.read_json(data)
 

# df = get_wtd_data(measured_quantity='water_table_1', output_mode='json', n_records=100)
def get_day_rainfall(): # WARNING: I DO NOT KNOW WHETHER THIS IS ACTUALLY DAILY RAINFALL OR NOT
    df_weather = get_instantaneous_weather_data()
    return float(df_weather['davis_current_observation']['rain_day_in'])

  

def write_raster_to_disk(raster, out_filename, in_filename=r"data/Strat4/DTM_metres_clip.tif"):
    import rasterio
    with rasterio.open(in_filename) as src: #src file is needed to output with the same metadata and attributes
        profile = src.profile
    _, wtd_old , _, _, _ = preprocess_data.read_preprocess_rasters(in_filename, in_filename, in_filename, in_filename, in_filename)

    
    profile.update(nodata = None) # overrun nodata value given by input raster
    profile.update(width = wtd_old.shape[1]) # Shape of rater is changed for hydro simulation inside read_preprocess_rasters. Here we take that shape to output consistently.
    profile.update(height = wtd_old.shape[0])
    # profile.update(dtype='float32', compress='lzw') # What compression to use?
    profile.update(dtype='float32') # instead of 64. To save space, we don't need so much precision. float16 is not supported by GDAL, check: https://github.com/mapbox/rasterio/blob/master/rasterio/dtypes.py

    with rasterio.open(out_filename, 'w', **profile) as dst:
        dst.write(raster.astype(dtype='float32'), 1)
        
    return 0


"""
GET WEATHER DATA
"""
P = np.array([get_day_rainfall()]) * 25.4  # From inches to mm. array type is to allow for list of precip. Usually, single value is used.

"""
READ PREVIOUS WTD
and DEM, peat type and peat depth rasters
"""
output_folder = r'./WTD'
absolute_path_datafolder = os.path.abspath('./data')
relative_datafolder = r"data/Strat4"

list_fn_with_WTD_in_name = [fn for fn in os.listdir(output_folder) if 'WTD' in fn]
list_fn_with_WTD_in_name.sort()
wtd_old_fn = output_folder + '/' + list_fn_with_WTD_in_name[-1] # latest file with WTD in its name
dem_rst_fn = relative_datafolder + r"/DTM_metres_clip.tif"
can_rst_fn = relative_datafolder + r"/canals_clip.tif"
peat_depth_rst_fn = relative_datafolder + r"/Peattypedepth_clip.tif" # peat depth, peat type in the same raster
# params_fn = r"C:\Users\03125327\github\dd_winrock\data\params.xlsx" # Luke NEW
params_fn = absolute_path_datafolder + "/params.xlsx" 

_, wtd_old , dem, peat_type_arr, peat_depth_arr = preprocess_data.read_preprocess_rasters(wtd_old_fn, can_rst_fn, dem_rst_fn, peat_depth_rst_fn, peat_depth_rst_fn)


"""
RUN HYDROLOGICAL MODEL
"""
DAYS = 1
N_BLOCKS = 0


# Generate adjacency matrix, and dictionary. Need to do this every time?
CNM, cr, c_to_r_list = preprocess_data.gen_can_matrix_and_raster_from_raster(can_rst_fn=can_rst_fn, dem_rst_fn=dem_rst_fn)

# Read parameters
PARAMS_df = preprocess_data.read_params(params_fn)
CANAL_WATER_LEVEL = PARAMS_df.canal_water_level[0]
DIRI_BC = PARAMS_df.diri_bc[0]; HINI = PARAMS_df.hini[0];
ET = np.array([PARAMS_df.ET[0]])
TIMESTEP = PARAMS_df.timeStep[0]; KADJUST = PARAMS_df.Kadjust[0]

print(">>>>> WARNING, OVERWRITING PEAT DEPTH")
peat_depth_arr[peat_depth_arr < 2.] = 2.

# catchment mask
catchment_mask = np.ones(shape=dem.shape, dtype=bool)
catchment_mask[np.where(dem<-10)] = False # -99999.0 is current value of dem for nodata points.

# peel the dem. Only when dem is not surrounded by water
boundary_mask = utilities.peel_raster(dem, catchment_mask)
 
# after peeling, catchment_mask should only be the fruit:
catchment_mask[boundary_mask] = False

# soil types and soil physical properties and soil depth:
peat_type_masked = peat_type_arr * catchment_mask
peat_bottom_elevation = - peat_depth_arr * catchment_mask # meters with respect to dem surface. Should be negative!
#

h_to_tra_and_C_dict, K = hydro_utils.peat_map_interp_functions(Kadjust=KADJUST) # Load peatmap soil types' physical properties dictionary

tra_to_cut = hydro_utils.peat_map_h_to_tra(soil_type_mask=peat_type_masked,
                                           gwt=peat_bottom_elevation, h_to_tra_and_C_dict=h_to_tra_and_C_dict)
sto_to_cut = hydro_utils.peat_map_h_to_sto(soil_type_mask=peat_type_masked,
                                           gwt=peat_bottom_elevation, h_to_tra_and_C_dict=h_to_tra_and_C_dict)
sto_to_cut = sto_to_cut * catchment_mask.ravel()

srfcanlist =[dem[coords] for coords in c_to_r_list]

n_canals = len(c_to_r_list)


# HANDCRAFTED WATER LEVEL IN CANALS. CHANGE WITH MEASURED, IDEALLY.
oWTcanlist = [x - CANAL_WATER_LEVEL for x in srfcanlist]

wt_canals = utilities.place_dams(oWTcanlist, srfcanlist, 0, [], CNM)

ny, nx = dem.shape
dx = 1.; dy = 1. # metres per pixel  (Actually, pixel size is 100m x 100m, so all units have to be converted afterwards)

boundary_arr = boundary_mask * (dem - DIRI_BC) # constant Dirichlet value in the boundaries

ele = dem * catchment_mask

# Get a pickled phi solution (not ele-phi!) computed before without blocks, independently,
# and use it as initial condition to improve convergence time of the new solution
retrieve_transient_phi_sol_from_pickled = False
if retrieve_transient_phi_sol_from_pickled:
    with open(r"pickled/transient_phi_sol.pkl", 'r') as f:
        phi_ini = pickle.load(f)
    print("transient phi solution loaded as initial condition")
    
else:
    phi_ini = ele + 0.0 #initial h (gwl) in the compartment.
    phi_ini = phi_ini * catchment_mask
       
wt_canal_arr = np.zeros((ny,nx)) # (nx,ny) array with wt canal height in corresponding nodes
for canaln, coords in enumerate(c_to_r_list):
    if canaln == 0: 
        continue # because c_to_r_list begins at 1
    wt_canal_arr[coords] = wt_canals[canaln] 


wtd = hydro.hydrology('transient', nx, ny, dx, dy, DAYS, ele, phi_ini, catchment_mask, wt_canal_arr, boundary_arr,
                      peat_type_mask=peat_type_masked, httd=h_to_tra_and_C_dict, tra_to_cut=tra_to_cut, sto_to_cut=sto_to_cut,
                      diri_bc=DIRI_BC, neumann_bc = None, plotOpt=True, remove_ponding_water=True,
                      P=P, ET=ET, dt=TIMESTEP)


print('COMPLETED')


"""
WRITE NEXT WTD and output info to file
"""
datetime_now = time.strftime("%Y"+"_"+"%m"+"_"+"%d-%H"+"_"+"%M"+"_"+"%S")
out_filename= output_folder + '/WTD_' + datetime_now + '.tif'
write_raster_to_disk(wtd, out_filename=out_filename)