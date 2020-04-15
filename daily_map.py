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
import argparse
import sys
import pickle
from pathlib import Path
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

def get_historic_P_ET(f_path):   
    # Read P and ET from weather station data.
    df_w = pd.read_csv(f_path, delimiter=',', skiprows=5, engine='python', decimal=',') # thousands reads comma as dot!
    df_w[['Date','Time', 'Meridiam']] = df_w['Date & Time'].str.split(" ",expand=True,) # split date and time into 2 columns
    P = df_w.groupby('Date', sort=False)['Rain - mm'].sum()
    ET = df_w.groupby('Date', sort=False)['ET - mm'].sum() # This ET is too big! And fluctuates very strangely
    dates = P.index
    return P.to_numpy(), ET.to_numpy(), dates.to_list()
  

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

def write_WTD_to_file(wtd, wtd_old_fn, hp, date):
    """
    Writes wtd raster to disk in the same folder as the previous wtd raster

    Parameters
    ----------
    wtd : numpy raster
        freshly computed wtd raster
    wtd_old_fn : str
        filename for the old wtd raster
    hp : bool
        HISTORIC_PRECIPITATION boolean read from command-line.
    date : str
        String describing date and time. Examples: '2020_04_15' or '2020_04_15-12_30_29'

    Returns
    -------
    None

    """
    if hp: # historic precipitation mode
        out_filename = WTD_folder / ('HP_WTD_' + date + '.tif')
    else:
        out_filename = WTD_folder / ('WTD_' + date + '.tif')
     
    write_raster_to_disk(wtd, out_filename=out_filename, in_filename=wtd_old_fn)
    
    return 0

def previous_wtd_fname(WTD_folder, hp):
    """
    Finds and relevant previous wtd raster.

    Parameters
    ----------
    WTD_folder : Pathlib Path object
        Folder where WTD are read and written.
    hp : bool
        Command-line argument HISTORIC_PRECIPITATION described above.
        If True, looks for previous wtd raster filenames that begin by HP_WTD
        If False, looks for previous wtd raster filenames that begin by WTD

    Returns
    -------
    wtd_old_fn : str
        File name of the previous wtd raster file

    """
    if hp:
        find_queue = 'HP_WTD*.tif'
    else:
        find_queue = 'WTD*.tif'
    list_fn_with_WTD_in_name = [fn for fn in WTD_folder.glob(find_queue)]
    list_fn_with_WTD_in_name.sort()
    wtd_old_fn =  list_fn_with_WTD_in_name[-1] # latest file with WTD in its name

    return wtd_old_fn

def date_format(date):
    """
    Gets date in the format coming from the weather station data [d/m/yy].
    Returns date in proper format for incremental file saving and reading [yyyy/mm/dd]

    Parameters
    ----------
    date : string
        Date in d/m/yy format. Default format from historic weather station data.

    Returns
    -------
    date_formatted : string
        date in yyyy_mm_dd format.

    """
    ymd = date.split('/')[::-1]
    yyyy = '20' + ymd[0]
    if len(ymd[1]) == 2:
        mm = ymd[1]
    else:
        mm = '0' + ymd[1]
    if len(ymd[2]) == 2:
        dd = ymd[2]
    else:
        dd = '0' + ymd[2]
    
    return yyyy + '_' + mm + '_' + dd


"""
Parse command-line arguments
"""
parser = argparse.ArgumentParser(description='Run hydrology')
parser.add_argument('-hp','--histprep', action='store_true', help='Runs with ALL historic precipitation data from file')
args = parser.parse_args()

HISTORIC_PRECIPITATION = args.histprep

"""
Read DEM, peat type and peat depth rasters
"""
filenames_df = pd.read_excel('file_pointers.xlsx', header=2, dtype=str)

dem_rst_fn = Path(filenames_df[filenames_df.Content == 'DEM'].Path.values[0])
can_rst_fn = Path(filenames_df[filenames_df.Content == 'canal_raster'].Path.values[0])
peat_depth_rst_fn = Path(filenames_df[filenames_df.Content == 'peat_depth_raster'].Path.values[0])
params_fn = Path(filenames_df[filenames_df.Content == 'parameters'].Path.values[0])
WTD_folder = Path(filenames_df[filenames_df.Content == 'WTD_input_and_output_folder'].Path.values[0])
weather_fn = Path(filenames_df[filenames_df.Content == 'historic_precipitation'].Path.values[0])



"""
GET WEATHER DATA
"""
if HISTORIC_PRECIPITATION:
    # command-line argument forces execution of the hydrological model for ALL 
    # precipitation data in weather_fn. 
    precip, _, dates = get_historic_P_ET(weather_fn)
    dates = [date_format(i) for i in dates] # good format

else:
    precip = np.array([get_day_rainfall()]) * 25.4  # From inches to mm. array type is to allow for list of precip. Usually, single value is used.

"""
LOOP FOR HISTORICAL PRECIPITATION DATA
If only daily precipitation, then precip is a list of length 1.
"""    
for d, P in enumerate(precip):
    
    if HISTORIC_PRECIPITATION and d==0:
        wtd_old = 0. # The initial condition is fully saturated.
        wtd_old_fn = dem_rst_fn # this works for raster reading and writing functions
        _, _ , dem, peat_type_arr, peat_depth_arr = preprocess_data.read_preprocess_rasters(wtd_old_fn, can_rst_fn, dem_rst_fn, peat_depth_rst_fn, peat_depth_rst_fn)

    else:
        wtd_old_fn = previous_wtd_fname(WTD_folder, hp=HISTORIC_PRECIPITATION)
        _, wtd_old , dem, peat_type_arr, peat_depth_arr = preprocess_data.read_preprocess_rasters(wtd_old_fn, can_rst_fn, dem_rst_fn, peat_depth_rst_fn, peat_depth_rst_fn)

    
    """
    RUN HYDROLOGICAL MODEL
    """
    DAYS = 1 # number of days with daily timestep for hydrological module
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
        phi_ini = ele + wtd_old #initial h (gwl) in the compartment.
        phi_ini = phi_ini * catchment_mask
           
    wt_canal_arr = np.zeros((ny,nx)) # (nx,ny) array with wt canal height in corresponding nodes
    for canaln, coords in enumerate(c_to_r_list):
        if canaln == 0: 
            continue # because c_to_r_list begins at 1
        wt_canal_arr[coords] = wt_canals[canaln] 
    
    
    wtd = hydro.hydrology('transient', nx, ny, dx, dy, DAYS, ele, phi_ini, catchment_mask, wt_canal_arr, boundary_arr,
                          peat_type_mask=peat_type_masked, httd=h_to_tra_and_C_dict, tra_to_cut=tra_to_cut, sto_to_cut=sto_to_cut,
                          diri_bc=DIRI_BC, neumann_bc = None, plotOpt=False, remove_ponding_water=True,
                          P=np.array([P]), ET=ET, dt=TIMESTEP)
    
    
    print('COMPLETED')
    
    
    """
    WRITE NEXT WTD and output info to file
    """       
    
    if HISTORIC_PRECIPITATION:
        datetime_write = dates[d]
    else:
        datetime_write = time.strftime("%Y"+"_"+"%m"+"_"+"%d-%H"+"_"+"%M"+"_"+"%S")
    
    write_WTD_to_file(wtd, wtd_old_fn, hp=HISTORIC_PRECIPITATION, date=datetime_write)