# Danish Meteorological institut weather API script
@ Author: Victor With

This script is used by the students and researcher at Aalborg university at the Department of the Built Environment. The scope of this work is to provide weather data for user defined project site and time period, where the closest weather stations is used to provide the wished weather parameters. This has been used for creating custom weather files for the Building simulation program, BSim.

The `DMI_weather_data_collector.py` is used to get data from DMI database through their API. For this to work the user must provide some information ("project site coordinates", "list of weather parameters", "time period",  and other information stated in the script.

The `handle_nan_values.py` is used after `DMI_weather_data_collector.py` to quickly check the overall data quality, and gives some option to handle missing values ("interpolating" and "replace missing values with a number"). 
