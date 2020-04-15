# Dosan daily WTD map
Gets weather data and produces daily WTD predictions for the Dosan area.

## ToDo
 - rasterio and Proj have some trouble finding proj.db. They return:
```
proj_create: Cannot find proj.db
proj_create: no database context specified
```
It doesn't affect the execution (that I know of), but is a pain in the ass to look at.
To solve this, take a look at: 
- https://github.com/conda-forge/rasterio-feedstock/issues/123
- https://gis.stackexchange.com/questions/326968/ogr2ogr-error-1-proj-pj-obj-create-cannot-find-proj-db

## Installation
In a new environment within Conda with minimal packages:

### Ubuntu 18.04 LTS
```
conda create -n [name of environment] -c conda-forge python=3 numpy scipy rasterio fipy matplotlib pandas xlrd
```

### Windows 10
```
conda create -n [name of environment] -c conda-forge python=3 fipy rasterio pandas xlrd requests
```

If you're interested in installing it alongside Spyder, only the python 3.6 version works as of March, 2020:
```
conda create -n [name of environment] -c conda-forge python=3.6 fipy rasterio xlrd
```

Optional packages:
  - ``` spyder```: IDE for Python. Can be added to the list above.



## How to use?
daily_map.py takes the daily weather data from weatherlink and produces a prediction of the wtd.

### [Optional] execute for historic precipitation data
In order to run the model with historical data, execute the program in the command line as

```python daily_map -hp```

The model will run with all the historical data contined in the .csv file specified in file_pointers.xlsx

In order to change the range of the simulation, carefully edit the .csv file to the range required.
It is crucial to maintain the format. When doing so, the water table  begins the simulation at the surface, i.e., in fully saturated conditions.
The program creates raster files whose name begins with 'HP_WTD'. Those files must be removed from the folder for new historical precipitation data runs.
