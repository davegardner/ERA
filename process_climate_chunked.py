#!/usr/bin/env python3
"""
Memory-efficient version: Process climatology in chunks to avoid memory issues.
Processes one day at a time across all years.
"""

import xarray as xr
import numpy as np
import pandas as pd
import subprocess
import os

print("📊 Building climatological 'typical year' (chunked processing)...")

# Initialize output arrays
files = sorted([f"era5_data/{f}" for f in os.listdir("era5_data") if f.endswith("_natl.nc")])
print(f"  Found {len(files)} yearly files")

# Get dimensions from first file
ds_sample = xr.open_dataset(files[0])
n_lat = len(ds_sample.latitude)
n_lon = len(ds_sample.longitude)
lat_vals = ds_sample.latitude.values
lon_vals = ds_sample.longitude.values
ds_sample.close()

# Initialize output arrays for 365 days * 24 hours
n_times = 365 * 24
u10_clim = np.zeros((n_times, n_lat, n_lon), dtype=np.float32)
v10_clim = np.zeros((n_times, n_lat, n_lon), dtype=np.float32)

print(f"  Output shape: {u10_clim.shape}")
print(f"  Memory required: ~{u10_clim.nbytes * 2 / 1024 / 1024:.1f} MB")

# Process day by day
time_idx = 0
for day in range(1, 366):
    print(f"  Processing day {day}/365...")
    
    for hour in range(24):
        # Collect data for this day/hour across all years
        u10_values = []
        v10_values = []
        
        for file in files:
            ds = xr.open_dataset(file)
            
            # Filter for this specific day and hour (excluding leap days)
            dayofyear = ds['valid_time'].dt.dayofyear
            hour_of_day = ds['valid_time'].dt.hour
            
            mask = (dayofyear == day) & (hour_of_day == hour)
            
            if mask.sum() > 0:
                u10_values.append(ds['u10'].where(mask, drop=True).values[0])
                v10_values.append(ds['v10'].where(mask, drop=True).values[0])
            
            ds.close()
        
        # Average across years
        if len(u10_values) > 0:
            u10_clim[time_idx] = np.mean(u10_values, axis=0)
            v10_clim[time_idx] = np.mean(v10_values, axis=0)
        
        time_idx += 1

print("  Creating output dataset...")
# Create time coordinate
typical_times = pd.date_range("2001-01-01", periods=365*24, freq="h")

# Create dataset
ds_out = xr.Dataset(
    {
        'u10': (['time', 'latitude', 'longitude'], u10_clim),
        'v10': (['time', 'latitude', 'longitude'], v10_clim),
    },
    coords={
        'time': typical_times,
        'latitude': lat_vals,
        'longitude': lon_vals,
    }
)

# Add attributes
ds_out['u10'].attrs = {'long_name': '10 metre U wind component', 'units': 'm s**-1'}
ds_out['v10'].attrs = {'long_name': '10 metre V wind component', 'units': 'm s**-1'}
ds_out.attrs = {'title': 'ERA5 Climatological Average Year (1940-1945)', 'source': 'ERA5 reanalysis'}

# Save
nc_out = "era5_typical_year_10m_wind_natlantic_chunked.nc"
print(f"💾 Saving NetCDF: {nc_out}")
ds_out.to_netcdf(nc_out)

# Convert to GRIB2
grib_out = "era5_typical_year_10m_wind_natlantic_chunked.grb2"
print(f"🌀 Converting to GRIB2: {grib_out}")
try:
    subprocess.run(["cdo", "-f", "grb2", "copy", nc_out, grib_out], check=True)
    print("✅ Done!")
    print(f"Output files:")
    print(f"  NetCDF: {nc_out}")
    print(f"  GRIB2: {grib_out}")
except subprocess.CalledProcessError as e:
    print(f"⚠️  CDO conversion failed: {e}")
    print(f"NetCDF file created: {nc_out}")
