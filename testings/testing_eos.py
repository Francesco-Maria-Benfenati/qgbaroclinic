# -*- coding: utf-8 -*-
"""
Created on Thu May  5 17:49:21 2022

@author: Francesco Maria
"""
# ======================================================================
# THIS FILE INCLUDES PART OF THE TESTS FOR FUNCTIONS IMPLEMENTED
# IN COMPUTING THE BAROCLINIC ROSSBY RADIUS ...
# ======================================================================
import xarray
import numpy as np
from scipy import interpolate
from hypothesis import given
import hypothesis.strategies as st

#=======================================================================
# Testing the functions for computing Potential Density & Brunt-Vaisala
# frequency. (See file 'eos.py')
#=======================================================================
import sys 
sys.path.append('..')
import OBM.eos as eos

#-----------------------------------------------------------------------
#                     Testing _compute_rho()
#-----------------------------------------------------------------------


def test_compute_rho_pure_water():
    """
    Test if _compute_rho() gives correct ref density at atm press. for  
    pure water (Sal = 0 PSU) at Temperature = 5, 25 °C.
    Reference values may be found within 
    'Algorithms for computation of fundamental properties of seawater'
    (UNESCO, 1983. Section 3, p.19)
    """
    
    ref_Sal = 0 #PSU
    ref_Temp = [5, 25] #°C
    ref_rho = [999.96675, 997.04796] #kg/m^3
    out_rho=[]
    
    out_rho.append(eos._compute_rho(ref_Temp[0], ref_Sal))
    out_rho.append(eos._compute_rho(ref_Temp[1], ref_Sal))
    
    error = 3.6e-03 #kg/m^3
    assert np.allclose(ref_rho, out_rho, atol=error)


def test_compute_rho_standard_seawater():
    """
    Test if _compute_rho() gives correct ref density at atm press. for 
    standard seawater (Sal = 35 PSU) at Temperature = 5, 25 °C.
    Reference values may be found within 
    'Algorithms for computation of fundamental properties of seawater'
    (UNESCO, 1983. Section 3, p.19)
    """
    
    ref_Sal = 35 #PSU
    ref_Temp = [5, 25] #°C
    ref_rho = [1027.67547, 1023.34306] #kg/m^3
    out_rho=[]

    out_rho.append(eos._compute_rho(ref_Temp[0], ref_Sal))
    out_rho.append(eos._compute_rho(ref_Temp[1], ref_Sal))
        
    error = 3.6e-03 #kg/m^3
    assert np.allclose(ref_rho, out_rho, atol=error)


#-----------------------------------------------------------------------
#              Testing _compute_K_0(), _compute_A(), _compute_B()
#-----------------------------------------------------------------------


def test_compute_bulk_modulus_K():
    """
    Test if the bulk modulus of seawater K(S, temp, press) is computed
    correctly adding results of _compute_K_0(), _compute_A(),
    _compute_B() functions.
    Reference values may be found within 'A new high pressure equation
    of state forseawater', Fig. 7 (Millero et al, 1980).
    
    *** NOTE:                                                        ***
            as a matter of reference values achievable through papers,
            the three functions can not be tested individually but 
            together.                                                
    """
    
    ref_Sal = [0, 35] #Salinity (PSU)
    ref_Temp = [0, 25] #Temperature (°C)
    P = 1000 #Pressure (bar)
    ref_K = [22977.21, 24992.00, 25405.10, 27108.95] #Ref. Bulk Modulus (bar)
    
    out_K=[]
    for temp in ref_Temp:
        for sal in ref_Sal:
            K_0 = eos._compute_K_0(temp, sal)
            A = eos._compute_A(temp, sal)
            B = eos._compute_B(temp, sal)
            K = K_0 + A*P + B*(P**2)
            out_K.append(K)
            
    error = 1e-03 #kg/m^3
    assert np.allclose(ref_K, out_K, atol=error)


#-----------------------------------------------------------------------
#                     Testing compute_density()
#-----------------------------------------------------------------------
 

def test_compute_density_pure_water():
    """
    Test if _compute_density() gives correct density for pure water 
    (Sal = 0 PSU) at Temperature = 5, 25 °C, P=10000 dbar (=1000 bar).
    Reference values may be found within 
    'Algorithms for computation of fundamental properties of seawater'
    (UNESCO, 1983. Section 3, p.19)
    """
    
    ref_Sal = 0 #PSU
    ref_P = 1000 #bar (1 bar = 10 dbar)
    ref_density = [1044.12802, 1037.90204] #kg/m^3
    ref_Temp = [5, 25] #°C
    
    # Compute Density.
    out_rho=[]
    out_rho.append(eos.compute_density(ref_P, ref_Temp[0], ref_Sal))
    out_rho.append(eos.compute_density(ref_P, ref_Temp[1], ref_Sal))
        
    error = 1e-06 #kg/m^3
    assert np.allclose(ref_density, out_rho, atol=error)


def test_compute_density_seawater():
    """
    Test if _compute_density() gives correct density for standad 
    seawater (Sal = 35 PSU) at Temperature = 5, 25 °C, P=10000 dbar 
    (=1000 bar).
    Reference values may be found within 
    'Algorithms for computation of fundamental properties of seawater'
    (UNESCO, 1983. Section 3, p.19)
    """
    
    ref_Sal = 35 #PSU
    ref_P = 1000 #bar
    ref_Temp = [5, 25] #°C
    ref_rho = [1069.48914, 1062.53817] #kg/m^3
    # Compute Density.
    out_rho=[]
    out_rho.append(eos.compute_density(ref_P, ref_Temp[0], ref_Sal))
    out_rho.append(eos.compute_density(ref_P, ref_Temp[1], ref_Sal))   
    error = 1e-06 #kg/m^3
    assert np.allclose(ref_rho, out_rho, atol=error)


#-----------------------------------------------------------------------
#                    Testing compute_BruntVaisala_freq_sq()
#-----------------------------------------------------------------------
from OBM.eos import compute_BruntVaisala_freq_sq as compute_BVsq
    
      
@given(arr_end = st.integers(3,100))
def test_compute_mean_dens_1D_input(arr_end):
    """
    Test if compute_BVsq() returns density input array when it is 1D,
    without computing the mean.
    """
    
    depth = np.linspace(0, arr_end, 30) 
    arr_1D =  np.arange(0, 30) 
    dims_1D = 'depth'
    trial_1D_array = xarray.Variable(dims_1D, arr_1D)
    mean_dens = compute_BVsq(depth, trial_1D_array)[1]
    
    f = interpolate.interp1d(depth, arr_1D, 
                              fill_value = 'extrapolate', kind = 'linear')
    z = np.linspace(0, arr_end, arr_end+1)
    expected_mean_dens = f(z)

    assert np.array_equal(mean_dens, expected_mean_dens)


@given(arr_end = st.integers(3,100))
def test_compute_mean_dens_2D_input(arr_end):
    """
    Test if compute_BVsq() computes the mean density correctly when 
    2D input arrays.
    """
    
    depth = np.linspace(0, arr_end, 50) 
    arr =  np.arange(0, 50) 
    len_lat = 5
    arr_2D = np.tile(arr, (len_lat,1))
    dims_2D = ('depth', 'lat')
    trial_2D_array = xarray.Variable(dims_2D, arr_2D)
    mean_dens = compute_BVsq(depth, trial_2D_array)[1]
    expected_mean_dens = np.mean(arr_2D, axis = 0)
    
    f = interpolate.interp1d(depth, expected_mean_dens, 
                              fill_value = 'extrapolate', kind = 'linear')
    z = np.linspace(0, arr_end, arr_end+1)
    interp_mean_dens = f(z)
    
    assert np.array_equal(mean_dens, interp_mean_dens)

    
@given(arr_end = st.integers(3,100))
def test_compute_mean_dens_3D_input(arr_end):
    """
    Test if compute_BVsq() computes the mean density correctly when 
    3D input arrays.
    """
    
    depth = np.linspace(0, arr_end, 75) 
    arr =  np.arange(0, 75)  
    len_lat = 5
    len_lon = 3
    dims_3D = ('depth', 'lat', 'lon')
    arr_3D = np.empty((len(depth), len_lat, len_lon))
    for i in range(len(depth)):
        arr_3D[i,:,:] = np.tile(arr[i], (len_lat, len_lon)) 
    trial_3D_array = xarray.Variable(dims_3D, arr_3D)
    mean_dens = compute_BVsq(depth, trial_3D_array)[1]
    expected_mean_dens = np.mean(arr_3D, axis = (1,2))
    
    f = interpolate.interp1d(depth, expected_mean_dens, 
                              fill_value = 'extrapolate', kind = 'linear')
    z = np.linspace(0, arr_end, arr_end+1)
    interp_mean_dens = f(z)
    
    assert np.array_equal(mean_dens, interp_mean_dens)
 

def test_compute_BV_const_dens():
    """
    Test if compute_BVsq() computes the BV freq. squared correctly 
    in a known constant case 
    rho(z)=const --> N^2 = 0 .
    """
    
    len_lat = 5
    len_lon = 3
    # Theoretical case.
    depth = np.arange(0, 100)
    rho_0 = 1025 #kg/m^3
    theor_BV2 = np.full([len(depth)], 0.0)
    rho_3D = np.empty((len(depth), len_lat, len_lon))
    for i in range(len(depth)):
        rho_3D[i,:,:] = np.tile(rho_0, (len_lat, len_lon))
    # Output product.
    dims_3D = ('depth', 'lat', 'lon')
    
    density = xarray.Variable(dims_3D, rho_3D)
    out_BV2 = compute_BVsq(depth, density)[0]

    assert np.allclose(out_BV2, theor_BV2, atol=1e-08)
 

@given(a = st.floats(0, 50))
def test_compute_BV_linear_dens(a):
    """
    Test if compute_BVsq() computes the BV freq. squared correctly 
    in a known linear case
    rho(z) = a * z + rho_0, z < 0 --> N^2 = -g .
    """
    
    # Theoretical case.
    H = 1000
    depth = - np.arange(0, H+1)
    rho_0 = 1025 #(kg/m^3) #kg/m^3, ref. density
    a /= - H
    rho = a*depth + rho_0
    g = 9.806 # (m/s^2)
    theor_BV2 = - (g*a/rho_0) * np.ones(len(depth))
    # Output product.
    len_lat = 5
    len_lon = 3
    dims_3D = ('depth', 'lat', 'lon')
    rho_3D = np.empty((len(depth), len_lat, len_lon))
    for i in range(len(depth)):
        rho_3D[i,:,:] = np.tile(rho[i], (len_lat, len_lon)) 
    density = xarray.Variable(dims_3D, rho_3D)
    out_BV2 = compute_BVsq(depth, density)[0]
    
    assert np.allclose(out_BV2, theor_BV2, atol=1e-08)


@given(a = st.floats(0, 0.05))
def test_compute_BV_expon_dens(a):
    """
    Test if compute_BVsq() computes the BV freq. squared correctly 
    in a known exponential case 
    rho(z) = rho_0 * exp(a*z), z < 0 --> N^2 = -g*a*exp(a*z)
    """
    
    # Theoretical case.
    H = 1000
    depth = - np.arange(0, H+1)
    rho_0 = 1025 #(kg/m^3) #kg/m^3, ref. density
    a /= - H
    rho = rho_0*np.exp(a*depth) 
    g = 9.806 # (m/s^2)
    theor_BV2 = - g*a*np.exp(a*depth)
    # Output product.
    len_lat = 5
    len_lon = 3
    dims_3D = ('depth', 'lat', 'lon')
    rho_3D = np.empty((len(depth), len_lat, len_lon))
    for i in range(len(depth)):
        rho_3D[i,:,:] = np.tile(rho[i], (len_lat, len_lon)) 
    density = xarray.Variable(dims_3D, rho_3D)
    out_BV2 = compute_BVsq(depth, density)[0]

    error = 1e-08 #error related to finite differences (dx**2)
    assert np.allclose(out_BV2, theor_BV2, atol= error)
    

def test_compute_BVsq_NaNs_behaviour():
    """
    Test if in compute_BVsq() values which are NaNs becomes values due
    to interpolation.
    """
    
    depth = np.arange(1, 7)
    density = [1, np.nan, 3, 4, 5, np.nan]
    trial_dim = ('depth')
    trial_dens = xarray.Variable(trial_dim, density)
    output_N2 = compute_BVsq(depth, trial_dens)[0]
    where_NaNs = np.where(np.isnan(output_N2.values))[0]
    expected_indeces = np.array([])
    
    assert np.array_equal(where_NaNs, expected_indeces)
    
    
@given(arr_end = st.integers(3,100))
def test_compute_BVsq_output_attrs(arr_end):
    """
    Test if compute_BVsq() gives correct output attributes.
    """
    depth = np.arange(1, arr_end)
    arr = np.arange(1, arr_end)
    trial_dim = 'depth'
    trial_array = xarray.Variable(trial_dim, arr)
    N2_attrs = {'long_name': 'Brunt-Vaisala frequency squared.', 
                  'standard_name': 'N_squared', 
                  'units': '1/s^2', 'unit_long':'cycles per second squared.'}
    N2 = compute_BVsq(depth, trial_array)[0]
    assert N2.attrs == N2_attrs


@given(arr_end = st.integers(3,100))
def test_compute_BVsq_when_depth_not_1D(arr_end):
    """
    Test if compute_BVsq() gives error when input depth is not 1D.
    """
    
    depth = np.arange(1, arr_end)
    depth_2D = np.tile(depth, (4,1))
    density = np.arange(1, arr_end)
    trial_dim = ('depth')
    trial_dens = xarray.Variable(trial_dim, density)
    try:
        compute_BVsq(depth_2D, trial_dens)
    except ValueError:
        assert True
    else:
        assert False
          

@given(arr_end = st.integers(3,100))
def test_compute_BVsq_when_lenDepth_is_greater_than_lenDens(arr_end):
    """
    Test if compute_BVsq() gives error when input depth has length
    greater than density one.
    """
    
    depth = np.arange(1, arr_end + 1)
    density = np.arange(1, arr_end)
    trial_dim = ('depth')
    trial_dens = xarray.Variable(trial_dim, density)
    try:
        compute_BVsq(depth, trial_dens)
    except ValueError:
        assert True
    else:
        assert False
