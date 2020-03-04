# Dosan daily WTD map
Gets weather data and produces daily WTD predictions for the Dosan area.

## ToDo
 - Initialize model with long weather history
 - Write to pickle, read from pickled

## Installation
1. Create a new environment within Conda with minimal packages:

### Ubuntu 18.04 LTS
```
conda create -n [name of environment] -c conda-forge python=3 numpy scipy rasterio fipy matplotlib pandas xlrd
```

### Windows 10
```
conda create -n [name of environment] -c conda-forge python=3 fipy rasterio pandas xlrd
```

If you're interested in installing it alongside Spyder, only the python 3.6 version works as of March, 2020:
```
conda create -n [name of environment] -c conda-forge python=3.6 fipy rasterio xlrd
```

Optional packages:
  - ``` spyder```: IDE for Python. Can be added to the list above.

2. Don't forget to activate the new environment!

3. Clone or download this repository.

## How to use?
