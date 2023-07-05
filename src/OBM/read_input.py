# -*- coding: utf-8 -*-
"""
Created on Thu Apr  7 16:06:25 2022

@author: Francesco M. Benfenati
"""
# ======================================================================
# This file includes the functions implemented for reading the 
# user's configuration file and extract data from NetCDF input file
# containing Potential Temperature & Salinity fields.
# ======================================================================       
import json
import xarray
import numpy as np
import pandas as pd


def read_JSON_config_file( file_name,
                           section_key, title_key, items_key, 
                           name_key, type_key, value_key      ):
    """
    Reads JSON configuration file, returns configuration parameters. 

    Arguments
    ---------
    file_name : 'str'
        Name of (or path to) the JSON configuration file
    section_key, title_key, items_key, 
    name_key, type_key, value_key      : 'str'
        keys to dictionary values within JSON configuration file
        
        NOTE: config. file must have at least structure of type
        {'section_key': 
         [
          {'title_key': -section title-,
           'items_key': [
                     {'name_key': -item name-,
                      'type_key': -'float', 'string', 'int' or 'bool'-,
                      'value_key': -item value-}
                     ... 
                     ]
           }
           ...
          ]
         }
          
     Raises
     ------
     FileNotFoundError
         if JSON file name or path given is not found.
     JSONDecodeError
         if syntax is not correct in JSON file.
     KeyError
         if dictionary keys are not the expected ones.
         
    Returns
    -------
    config_param : 'dict'
        A dictionary containing the configuration parameters as found
        within JSON configuration file.
        Following the config. file, parameters are grouped together 
        in sections through subdictionaries. Within each subdictionary, 
        keys correspond to the names of items in each section.
        Values correspond to the value of each item within the section. 
    """
    
    in_file = open(file_name, 'r')
    # Load user's dictionary in JSON configuration file.
    user_dict = json.loads(in_file.read())
    
    # Print project title from JSON file to log file.
    project_title = user_dict['project_name']
    print('===========================================================')
    print('| * ', project_title, ' * ')
    print('===========================================================')
    
    # Create empty dictionary for configuration parameters.
    config_param = {}
    # Fill dictionary with keys and values from user's one.
    for section in user_dict[section_key]:  
        section_name = section[title_key]
        config_param[section_name] = {}
        for item in section[items_key]:  
            item_name = item[name_key]
            item_type = item[type_key]
            item_value = item[value_key]
            
            if item_type == ('float'): 
                config_param[section_name][item_name] = float(item_value)
            elif item_type == ('int'): 
                config_param[section_name][item_name] = int(item_value)
            elif item_type == ('bool'): 
                config_param[section_name][item_name] = bool(item_value)
            else: 
                config_param[section_name][item_name] = str(item_value)
    
    # Close input file.
    in_file.close()
    
    # Return dictionary containing configuration parameters.          
    return config_param


def extract_data_from_NetCDF_input_file(config_param):
    """
    Reads NetCDF input data, returns Potential Temperature & Salinity.

    Arguments
    ---------
    config_param : 'dict'
        A dictionary containing the configuration parameters grouped
        through subdictionaries.
        {'set_paths': 
             {'indata_path': -path to input NetCDF data file-,
              'input_file_name': -name of input NetCDF data file-},
         'set_dimensions': 
             {'lat_name': -name of latitude DIM in NetCDF file-,
              'lon_name': -name of longitude DIM in NetCDF file-,
              'depth_name': -name of depth DIM in NetCDF file-, 
              'time_name': -name of time DIM in NetCDF file- }, 
         'set_domain': 
             {'lat_min': -min value of latitude-, 
              'lat_max': -max value of latitude-,
              'lon_min': -min value of longitude-, 
              'lon_max': -max value of longitude- },
         'set_time': 
             {'starting_time': -averaging time period beginning-,
              'ending_time': -averaging time period ending- },
         'set_variables': 
             {'temperature_name': -name of temperature in NetCDF file-,
              'salinity_name': -name of salinity in NetCDF file-,
              'lat_var_name': -name of latitude VAR in NetCDF file-,
              'lon__var_name': -name of longitude VAR in NetCDF file-,
              'time_var_name': -name of time VAR in NetCDF file- }
         }
         
    Raises
    ------
    KeyError
        if dictionary keys are not the expected ones.
                           - OR -
        if variables name in config. file does not match the ones in
        NetCDF file.
    FileNotFoundError
        if NetCDF file name or path given is not found.
        
    Returns
    -------
    mean_temperature : <class 'numpy.ndarray'>
        time-averaged temperature 3D array (one time step)
    mean_salinity : <class 'numpy.ndarray'>
        time-averaged salinity 3D array (one time step)
                 
    The arrays dimensions are depth, latitude and longitude.
    """
    
    # Define input file path from configuration parameters.
    set_paths = config_param['set_paths']
    path_to_file = set_paths['indata_path']
    file_name = set_paths['input_file_name']
    
    # Open input file and extrapolates dataset.
    full_path = path_to_file + file_name
    in_data = xarray.open_dataset(full_path)
    
    # Store lat, lon, time and depth DIMENSIONS.
    set_dims = config_param['set_dimensions']
    lat_dim = set_dims['lat_name']
    lon_dim = set_dims['lon_name']
    depth_dim = set_dims['depth_name']
    time_dim = set_dims['time_name']

    # Store lat, lon, time and depth variables from NetCDF input file.
    set_vars = config_param['set_variables']
    lat_name = set_vars['lat_var_name']
    lon_name = set_vars['lon_var_name']
    time_name = set_vars['time_var_name']
    latitude = in_data.variables[lat_name].values
    longitude = in_data.variables[lon_name].values
    time = in_data.variables[time_name].values
    
    # Call external function for setting the domain boundaries.
    set_domain = config_param['set_domain']
    lat_min = set_domain['lat_min']
    lat_max = set_domain['lat_max']
    lon_min = set_domain['lon_min']
    lon_max = set_domain['lon_max']
    
    lat_min_idx, lat_max_idx = _find_nearest(latitude, [lat_min, lat_max])
    lon_min_idx, lon_max_idx = _find_nearest(longitude, [lon_min, lon_max])
    
    # Call external function for looking for the time period wanted.
    set_time =  config_param['set_time']
    start_time = set_time['starting_time']
    end_time = set_time['ending_time']
    start_tstep = _find_time_step(time, start_time)
    end_tstep = _find_time_step(time, end_time)
    
    #-------------------------------------------------------------------
    # Store temperature and salinity, taking the domain area needed 
    # by the user and averaging over time.
    #-------------------------------------------------------------------
    temp_name = set_vars['temperature_name']
    sal_name = set_vars['salinity_name']
    dimensions = [time_dim, depth_dim, lat_dim, lon_dim]
    indeces = [start_tstep, end_tstep, 
               lat_min_idx, lat_max_idx, lon_min_idx, lon_max_idx]
    
    temperature = in_data.variables[temp_name]
    salinity = in_data.variables[sal_name]
    
    # Mean Temperature
    mean_temperature = _compute_mean_var(temperature, dimensions, indeces)
    # Mean Salinity
    mean_salinity = _compute_mean_var(salinity, dimensions, indeces)
    # Mean latitude
    mean_lat = np.mean(latitude, axis=None)
    in_data.close()
    
    # Return temperature and salinity arrays (averaged in time)
    return mean_temperature.values, mean_salinity.values, mean_lat


def extract_mean_bathy_from_NetCDF_file(config_param):
    """
    Reads NetCDF bathymetry dataset, returns mean ocean depth.

    Arguments
    ---------
    config_param : 'dict'
        A dictionary containing the configuration parameters grouped
        through subdictionaries.
        {'set_bathymetry': 
             {'bathy_path': -path to bathy NetCDF data file-,
              'bathy_file_name': -name of bathy NetCDF data file-,
              
              'lat_name': -name of latitude DIM in NetCDF file-,
              'lon_name': -name of longitude DIM in NetCDF file-,
              
              'lat_var_name': -name of latitude VAR in NetCDF file-,
              'lon__var_name': -name of longitude VAR in NetCDF file-,
              'bathy_var_name': -name of bathy VAR in NetCDF file- }
            
         'set_domain': 
             {'lat_min': -min value of latitude-, 
              'lat_max': -max value of latitude-,
              'lon_min': -min value of longitude-, 
              'lon_max': -max value of longitude- }
         }
         
    Raises
    ------
    KeyError
        if dictionary keys are not the expected ones.
                           - OR -
        if variables name in config. file does not match the ones in
        NetCDF file.
    FileNotFoundError
        if NetCDF file name or path given is not found.
        
    Returns
    -------
    mean_bathymetry: <class 'numpy.ndarray'> (0-dimensional)
        mean ocean depth of the considered region
                 
    """
    
    # Define bathy file path from configuration parameters.
    set_bathy = config_param['set_bathymetry']
    path_to_file = set_bathy['bathy_path']
    file_name = set_bathy['bathy_file_name']
    
    # Open bathy file and extrapolates dataset.
    full_path = path_to_file + file_name
    bathy_data = xarray.open_dataset(full_path)
    
    # Store lat, lon DIMENSIONS.
    lat_dim = set_bathy['lat_name']
    lon_dim = set_bathy['lon_name']

    # Store lat, lon variables from NetCDF bathy file.
    lat_name = set_bathy['lat_var_name']
    lon_name = set_bathy['lon_var_name']
    latitude = bathy_data.variables[lat_name].values
    longitude = bathy_data.variables[lon_name].values
    
    # Call external function for setting the domain boundaries.
    set_domain = config_param['set_domain']
    lat_min = set_domain['lat_min']
    lat_max = set_domain['lat_max']
    lon_min = set_domain['lon_min']
    lon_max = set_domain['lon_max']
    
    lat_min_idx, lat_max_idx = _find_nearest(latitude, [lat_min, lat_max])
    lon_min_idx, lon_max_idx = _find_nearest(longitude, [lon_min, lon_max])
    
    # ------------------------------------------------------------------
    # Compute mean bathymetry.
    # ------------------------------------------------------------------
    bathy_name = set_bathy['bathy_var_name']
    bathymetry = bathy_data.variables[bathy_name]
    
    mean_bathy = _compute_mean_bathy(bathymetry, [lat_dim, lon_dim], 
                                                 [lat_min_idx, lat_max_idx, 
                                                  lon_min_idx, lon_max_idx])

    return mean_bathy.values


def extract_depth3D_from_NetCDF_file(config_param):
    """
    Reads NetCDF input data, returns 3D depth array.

    Arguments
    ---------
    config_param : 'dict'
        A dictionary containing the configuration parameters grouped
        through subdictionaries.
        {'set_paths': 
             {'indata_path': -path to input NetCDF data file-,
              'input_file_name': -name of input NetCDF data file-},
         'set_domain': 
             {'lat_min': -min value of latitude-, 
              'lat_max': -max value of latitude-,
              'lon_min': -min value of longitude-, 
              'lon_max': -max value of longitude- },
         'set_variables': 
             {'lat_var_name': -name of latitude VAR in NetCDF file-,
              'lon_var_name': -name of longitude VAR in NetCDF file-,
              'depth_var_name': -name of depth VAR in NetCDF file- }
         }
         
    Raises
    ------
    KeyError
        if dictionary keys are not the expected ones.
                           - OR -
        if variables name in config. file does not match the ones in
        NetCDF file.
    FileNotFoundError
        if NetCDF file name or path given is not found.
        
    Returns
    -------
    depth_3D : <class 'numpy.ndarray'>
        3D depth array
                 
    The array dimensions are depth, latitude and longitude.
    """
    
    # Define input file path from configuration parameters.
    set_paths = config_param['set_paths']
    path_to_file = set_paths['indata_path']
    file_name = set_paths['input_file_name']
    
    # Open input file and extrapolates dataset.
    full_path = path_to_file + file_name
    in_data = xarray.open_dataset(full_path)

    # Store lat, lon, time and depth variables from NetCDF input file.
    set_vars = config_param['set_variables']
    lat_name = set_vars['lat_var_name']
    lon_name = set_vars['lon_var_name']
    depth_name = set_vars['depth_var_name']
    latitude = in_data.variables[lat_name].values
    longitude = in_data.variables[lon_name].values
    depth = in_data.variables[depth_name].values
    
    # Call external function for setting the domain boundaries.
    set_domain = config_param['set_domain']
    lat_min = set_domain['lat_min']
    lat_max = set_domain['lat_max']
    lon_min = set_domain['lon_min']
    lon_max = set_domain['lon_max']
    
    lat_min_idx, lat_max_idx = _find_nearest(latitude, [lat_min, lat_max])
    lon_min_idx, lon_max_idx = _find_nearest(longitude, [lon_min, lon_max])
    
    # ------------------------------------------------------------------
    # Store depth as an array with dimensions as temp and sal.
    # ------------------------------------------------------------------
    # Compute lengths
    len_lat = lat_max_idx + 1 - lat_min_idx
    len_lon = lon_max_idx + 1 - lon_min_idx
    len_depth = len(depth)
    # Create empty array.
    depth_3D = np.empty((len_depth, len_lat, len_lon))
    # Fill empty array.
    for i in range(len_depth):
        depth_3D[i,:,:] = np.tile(depth[i], (len_lat, len_lon)) 

    return depth_3D


def _find_time_step(time, user_time):
    """
    Find the index corresponding to the time step wanted by the user.

    Arguments
    ---------
    time : <class 'numpy.ndarray'>
        time array
    user_time : 'str'
        user time instant expressed as a string

    Raises
    ------
    ValueError
        if the wanted time step has not been found within the array.
       - or -
        if more than one index are found corresponding to the 
        wanted time date.

    Returns
    -------
    time_step : 'int'
        index corresponding to the time date looked for.
    """
    
    # Convert user time into pandas datetime.
    time_date = pd.to_datetime(user_time, errors='raise')
    time = pd.to_datetime(time, errors='raise')

    # Find index corresponding to user time date.
    time_index = np.where(time == time_date)[0]
    # Check if index has been found or if more than one has been found.
    if time_index.size == 0 : 
        raise ValueError(
            'Time step wanted has not been found within the dataset.')
    elif time_index.size > 1:
        raise ValueError(
             'There are more time steps with the same values:\
                 indeces array:', time_index)
    # Store index as int and return it.
    time_step = int(time_index)
    return time_step


def _find_nearest(array, values):
    """
    Find the index of nearest value to given ones, 
    within a  given array.
    """
    
    array = np.asarray(array)
    indeces = []
    for val in values:
        index = (np.abs(array - val)).argmin()
        indeces.append(index)
    return indeces


def _compute_mean_var(variable, dimensions, indeces):
    """
    Computing time averaged variable (temperature or salinity) in the
    desired region.
    """
    
    time_dim, depth_dim, lat_dim, lon_dim = dimensions
    start_tstep, end_tstep, lat_min, lat_max, lon_min, lon_max = indeces

    # Transpose temperature and salinity arrays for rearranging indeces.
    transposed_var = variable.transpose(time_dim, 
                                        depth_dim,
                                        lat_dim, 
                                        lon_dim, 
                                        ...        )
    # Store temperature and salinity values for the desired time period.
    var = transposed_var[start_tstep:end_tstep+1, :, 
                                  lat_min:lat_max+1, lon_min:lon_max+1]
    
    # Average temp and sal in time.
    mean_var = np.mean(var, axis = 0)
         
    return mean_var


def _compute_mean_bathy(bathymetry, dimensions, indeces):
    """
    Computing mean bathymetry in the considered region.
    """
    
    [lat_dim, lon_dim] = dimensions
    [lat_min, lat_max, lon_min, lon_max] = indeces

    # Store bathymetry.

    transposed_bathy = bathymetry.transpose(lat_dim, lon_dim, ... )
    bathymetry = transposed_bathy[lat_min:lat_max+1, lon_min:lon_max+1]

    # Mean sea depth.
    mean_bathy = np.mean(bathymetry, axis = None)
    
    return mean_bathy