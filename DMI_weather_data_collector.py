# -*- coding: utf-8 -*-
"""
Author: Victor With
Mail: von@build.aau.dk

This script gets user defined weather data from the DMI API and save the data
at a location on the user pc. 

The input the script require:
    Coordinates: [latitude, longitude]
    DMI defined parameters: [param1, param2, param3...]
    Time periode: Start, End
    Output file type: csv / excel / feather
    Output file name: filename
    
The output data file is as default saved in the same folder as this script.
    
Helpfull links:
    API documentation
    https://www.dmi.dk/friedata/dokumentation/apis
"""

# Load libraries
import requests
import json
import pytz
import datetime as dt
import pandas as pd
import numpy as np
from math import cos, asin, sqrt, pi

# =============================================================================
# Inputs
# =============================================================================
# Coordinatet (Latitude,  longitude)
# coords = [57, 9.9] # Aalborg
coords = [56.16961185893367, 10.149197405995057]
# To find the name of each station based on their stationId: https://www.dmi.dk/friedata/dokumentation/data/meteorological-observation-data-stations
# Map showing available weather stations https://www.dmi.dk/fileadmin/Rapporter/TR/tr13-08.pdf


# Timezone
# options:
#   Denmark: 1
#   Greenland: 2
#   Faroe island: 3
timezone = 1

# Parameters to get
# A parameter list can be found here: https://www.dmi.dk/friedata/dokumentation/meteorological-observations-data#codes
params = ['radia_glob', 'sun_last10min_glob', 'cloud_cover', 'cloud_height', 
          'temp_dry', 'temp_dew', 'precip_dur_past10min', 'wind_speed',
          'wind_dir', 'pressure', 'humidity']

# Average
# options:
#   10 min: 1
#   30 min: 2
#   60 min: 3
average = 3

# Time period
start_year = 2025
start_month = 1
start_day = 1
start_hour = 0

to_now = False # If True, it will get all data from start to the current time.
# if to_now is False, the below time will be used.
end_year = 2025
end_month = 12
end_day = 31
end_hour = 23


# File type
# Options:
#   csv: 1
#   excel: 2
#   feather: 3
#   json: 4
filetype = 1


# File name
filename = 'test_data'


# =============================================================================
# The script - PLEASE DO NOT TOUCH
# =============================================================================
#%% get data
# Returnere en liste med alle tilgænglige vejrstationer
def get_stations(**params):    
    url = 'https://opendataapi.dmi.dk/v2/metObs/collections/station/items'
    
    response = requests.get(url, params=params)
    status = response.status_code
    assert status == 200, f'status code is not 200, but {status}'
    
    data = json.loads(response.text)
    
    return data


# Retunere målte værdier fra vejrstationerne.
def get_weather_data(**params):
    url = 'https://opendataapi.dmi.dk/v2/metObs/collections/observation/items'

    response = requests.get(url, params=params)
    
    status = response.status_code
    assert status == 200, f'status code is not 200, but {status}'
    
    data = json.loads(response.text)
    
    return data


#%% calculate distance
# Jordens diameter bruges i funktionen distance
CONST_EARTH_DIAMETER = 12742    # km

# Beregner afstanden mellem to koordinator på en kugle.
def distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in km between two geographical points.
    Args:
        lat1 (float): Latitude of point 1.
        lon1 (float): Longitude of point 1.
        lat2 (float): Latitude of point 2.
        lon2 (float): Longitude of point 2.
    Returns:
        float: Haversine distance in km between point 1 and 2.
    """
    p = pi / 180.0
    a = 0.5 - cos((lat2 - lat1) * p) / 2.0 + cos(lat1 * p) * cos(lat2 * p) * (1.0 - cos((lon2 - lon1) * p)) / 2
    return CONST_EARTH_DIAMETER * asin(sqrt(a))


# Beregner aftstanden fra et givet punkt til alle DMIs vejrstationer som måler en specifik parameter
def get_closest_station(stations, coords, parameterID):
    stations = stations['features']
    
    lon1 = coords[1]
    lat1 = coords[0]
    
    min_dis = 100000
    min_station = '99999'
        
    for station in stations:
        if not parameterID in station['properties']['parameterId']:
            continue
        
        lon2 = station['geometry']['coordinates'][0]
        lat2 = station['geometry']['coordinates'][1]
        
        dis = distance(lat1, lon1, lat2, lon2)
        
        if min_dis > dis:
            min_dis = dis
            min_station = station['properties']['stationId']
    
        
    return min_station

#%% combining part
# Sikre at formattet af datetime er korrekt
def add_timezone(datetime):
    temp_datetime = tz.localize(datetime)
    return str(temp_datetime).replace(' ', 'T')


# Sætter start og slut tiden sammen, afhængig af hvordan start og end er difineret,
# da .. betyder man ikke definere en grænse.
def get_times(start, end) -> str:
    if start != None and end != None:
        assert start < end, f'Den angivet start tiden er højre end slut værdien. {start} - {end}'
    
    
    if start == None and end != None:
        start_string = '..'
        end_string = add_timezone(end)
    if start != None and end == None:
        start_string = add_timezone(start)
        end_string = '..'
    if start != None and end != None:
        start_string = add_timezone(start)
        end_string = add_timezone(end)
    if start == None and end == None:
        start_string = '..'
        end_string = '..'
        
    datetime_string = start_string + '/' + end_string
    
    print(datetime_string)
    
    return datetime_string

# Definere et tidskridt på 2 dage, da der er en begrænsing på hvor meget data
# man kan hente adgangen.
timestep = dt.timedelta(days=2)


# Kører et loop, som henter data ved brug modulerne, og konstrukturer dataet
# så det er nemt at hente.
def get_data_function(coords, params, start, end):

    stations = get_stations()
    
    
    stations = [get_closest_station(stations, coords, param) for param in params]
    
    
    final_data = []
    
    if end == None:
        end = dt.datetime.now()
    
    while True:
    
        temp_end = start + timestep
        
        if temp_end >= end:
            
            if temp_end - end > timestep:
                break
            else:
                temp_end = start + timestep-(temp_end-end)
                
        datetime_string = get_times(start, temp_end)
    
        for station, param in zip(stations, params):
        
            
            data = get_weather_data(
                                    stationId = station,
                                    parameterId = param,
                                    datetime=datetime_string
                                    )
            
            param_data = []
            
            for p_data in data['features']:
                temp_data = {'timestamp': p_data['properties']['observed'],
                             'value': p_data['properties']['value'],
                             'stationId': p_data['properties']['stationId'],
                             'parameterId': p_data['properties']['parameterId']}
                param_data.append(temp_data)
            
            
            final_data.append(pd.DataFrame(param_data))
    
    
        start += timestep
    
    
    final_data = pd.concat(final_data, axis=0, ignore_index=True)
    

    return final_data


def calc_average(data, average) -> pd.DataFrame:
    data['timestamp'] = (
        pd.to_datetime(data['timestamp'])
        .dt.tz_convert("europe/copenhagen")
        )
    if average == 1:
        average = '10min'
    elif average == 2:
        average = '30min'
    elif average == 3:
        average = '60min'
    
    df = []
    for param, df_temp in data.groupby(by='parameterId'):
        temp = df_temp[['timestamp', 'value']].resample(average, on='timestamp').mean()
        temp = temp.rename(columns={'value':param})
        df.append(temp)
    
    df = pd.concat(df, axis=1)
    
    return df


def connect_param_and_stations(data):
    params_station = data.groupby(['stationId','parameterId']).size()
    params_station = params_station.reset_index()[['stationId', 'parameterId']]
    return params_station


def MartinFrandsen_raw(data, filename) -> None:
    data = data[['timestamp','value']].set_index('timestamp')
    first, second = filename.split('.')[0], filename.split('.')[-1]
    first += '_raw'
    filename = '.'.join(first,second)
    data.to_csv(filename)


def Olena(df, filename) -> None:
    cols = df.columns.tolist()
    df['year'] = df.index.year
    df['month'] = df.index.month
    df['day'] = df.index.day
    df['hour'] = df.index.hour
    df['minute'] = df.index.minute
    df = df[['year', 'month', 'day', 'hour', 'minute'] + cols].reset_index(drop=True)
    
    
    params_station = data.groupby(['stationId','parameterId']).size()
    params_station = params_station.reset_index()[['stationId', 'parameterId']]
    
    with pd.ExcelWriter(filename) as writer:
        df.to_excel(writer, sheet_name='Data')
        params_station.to_excel(writer, sheet_name='stations', index=False)


def CSV(data, params_station, filename) -> None:
    # seperator = ";"
    # decimalpoint = "."
    data.to_csv(filename)
    ps_filename = filename.split('.')[0] + '-used_stations.csv'
    params_station.to_csv(ps_filename, sep=";", decimal=".", index=False)

def EXCEL(data, params_station, filename) -> None:
    data.index=data.index.astype(str)
    
    with pd.ExcelWriter(filename) as writer:
        df.to_excel(writer, sheet_name='Data')
        params_station.to_excel(writer, sheet_name='stations', index=False)
    
def FEATHER(data, params_station, filename) -> None:
    data = data.reset_index(drop=False)
    data.to_feather(filename)
    ps_filename = filename.split('.')[0] + '-used_stations.csv'
    params_station.to_csv(ps_filename, index=False)

def JSON(data, params_station, filename) -> None:
    data = data.reset_index(drop=False)
    data.to_json(filename, orient='records', date_format='iso', date_unit='s')
    ps_filename = filename.split('.')[0] + '-used_stations.csv'
    params_station.to_csv(ps_filename, index=False)

# Kører ovenstående funktioner.
if __name__ == '__main__':
    # Settings
    if timezone == 1:
        tz = pytz.timezone('Europe/Copenhagen')
    elif timezone == 2:
        tz = pytz.timezone('America/Godthab')
    elif timezone == 3:
        tz = pytz.timezone('Atlantic/Faroe')
    
    # Hvis begge er None, så er de bare al data der hentes
    start = dt.datetime(start_year, start_month, start_day,
                        start_hour, 0) # dansk tid
    if to_now:
        end = None
    else:
        end = dt.datetime(end_year, end_month, end_day,
                          end_hour, 10) 

    
    data = get_data_function(coords, params, start, end)
    if "wind_dir" in params:
        data.loc[
            (data["parameterId"] == "wind_dir") &
            (data["value"] == 0)
            ] = np.nan
    
    df = calc_average(data, average)
    params_station = connect_param_and_stations(data)
    if "cloud_cover" in params:
        df["cloud_cover"] = df["cloud_cover"] / 100
    if "humidity" in params:
        df["humidity"] = df["humidity"] / 100
    if "pressure" in params:
        df["pressure"] = df["pressure"] * 100
    
    
    if filetype == 1:
        filename += '.csv'
        CSV(df, params_station, filename)
    elif filetype == 2:
        filename += '.xlsx'
        EXCEL(df, params_station, filename)
    elif filetype == 3:
        filename += '.feather'
        FEATHER(df, params_station, filename)
    elif filetype  == 4:
        filename += '.json'
        JSON(df, params_station, filename)
    
