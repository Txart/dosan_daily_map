# Dosan daily WTD map
Gets weather data and produces daily WTD predictions for the Dosan area.

## ToDo


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
