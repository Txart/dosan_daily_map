import requests
import pandas as pd
import sys
if sys.version_info[0] < 3:  # Fork for python2 and python3 compatibility
    from StringIO import StringIO
else:
    from io import StringIO



#def get_wtd_data(measured_quantity='water_table_1', output_mode='csv', n_records=100):
#    """
#    Generates an API call for the chosen options and outputs the data from the dosan project server.
#    
#    INPUT
#        - collection: (str) 'measurements' or 'sensors'
#        - measured_quantity: (str) 'water_table_1' or 'water_table_2'
#        - output_mode: (str) 'csv' or 'json'
#        - n_records: (int) amount of records of data points to return. MAX 20000.
#    
#    OUTPUT
#        if output_mode == 'csv' returns the data in dataframe.
#        if output_mode == 'json' returns it in a single unicode string
#    """
#    api_key = '61b8b35c1a42075c2f2de046ffe1975c908bc41355bda38f15efcf9cb9e7'
#    api_url = "https://dashboard.sustainabilitytech.com/api/v1"
#    headers = {'Authorization': 'Basic ' + api_key}
#    body = {'limit': n_records, 'sort': {"created":1}}
#    
#    if n_records > 20000: raise ValueError('n_records must be below 20000')
#    
#    if collection == 'sensors':
#        api_url = api_url_base + 'sensors/'
#        body['fields'] = ({"created":1,"label":1,"projectId":1,"measureOffset":1,"devId":1,
#                            "unit":1,"latitude":1,"longitude":1,"mergedInto":1,"enabledSensorTypes":1})
#        
#        body['filter'] = {"projectId":"5c6a0f20868636437eaab987"}
#
#    body['filter'] = {"created":{"$gte":"Sun, 09 Feb 2020 22:00:00 GMT","$lte":"Mon, 10 Feb 2020 22:00:00 GMT"},
#                      "sensorTypeId":"5bb2e0ab1b0f4d3f1721518c",
#                      "projectId":"5c6a0f20868636437eaab987"}
#
#    if output_mode == 'csv':
#        api_url = api_url + 'csv'
#    elif output_mode == 'json':
#        api_url = api_url + 'json'
#    else:
#        raise ValueError('output_mode only accepts "csv" and "json" as values')
#    
#    # This is where the request happens
#    response = requests.request(method='POST', url=api_url, json=body, headers=headers)
#    print('HTTP response status code: ', response.status_code)
#    if response.status_code == 200:
#        if output_mode == 'csv':
#            data = response.text
#            strdata = StringIO(data)
#            return pd.read_csv(strdata)
#        
#        if output_mode == 'json':
#            return response.content.decode('utf-8')
#    else:
#        return None

#df = get_data(collection='measurements', measured_quantity='water_table_1', output_mode='csv', n_records=100)

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



def get_wt_data():
    api_key = '61b8b35c1a42075c2f2de046ffe1975c908bc41355bda38f15efcf9cb9e7'
    api_url = "https://dashboard.sustainabilitytech.com/api/v1"
    headers = {"Authorization": "Basic " + api_key, "Content-Type" : "application/json"}
    body = {'limit': 100, 'sort': {"created":-1}, 'custom':'apiMeasurements', 'format':'csv'}
    
    body['filter'] = {"created":{"$gte":"Sun, 09 Feb 2020 22:00:00 GMT","$lte":"Mon, 10 Feb 2020 22:00:00 GMT"},
                      "sensorTypeId":"5bb2e0ab1b0f4d3f1721518c",
                      "projectId":"5c6a0f20868636437eaab987"}
    
    # This is where the request happens
    response = requests.request(method='POST', url=api_url, json=body, headers=headers)
    print('HTTP response status code: ', response.status_code)
    data = response.text
    strdata = StringIO(data)
    return pd.read_csv(strdata)

df_wt = get_wt_data()

# LAST TRY with pages from pdf

#username = 'imambasuki'
#DID =  '001D0A00F65E' # DEVIDE ID
#password = 'putri061112'
#apiToken = 'CF4BCA6F352A46358FAF00E7E9009516'
#timestamp = 0 # all data
#def _timestamp(day, month, year, hour, minute):
#    vantageDateStamp = day + month * 32 + (year-2000)*512
#    vantageTimeStamp = 100*hour + minute
#    return vantageDateStamp, vantageTimeStamp
#
##headers request
#headers = "http://weatherlink.com/webdl.php?timestamp=" + str(timestamp) + "&user=" + DID + "&pass=" + password + "&action=headers"
#response = requests.request(method='GET', url=headers)
#print('HTTP response status code: ', response.status_code)
#
## data request
#data = "http://weatherlink.com/webdl.php?timestamp=" + str(timestamp) + "&user=" + DID + "&pass=" + password + "&action=data"
#response = requests.request(method='GET', url=data)
#print('HTTP response status code: ', response.status_code)

