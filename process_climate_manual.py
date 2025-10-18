#!/usr/bin/env python3
"""
Alternative approach: Manual averaging without groupby.
Uses direct indexing and numpy operations for better memory control.
"""

import xarray as xr
import numpy as np
import pandas as pd
import subprocess
import os
from datetime import datetime

print("📊 Building climatological 'typical year' (manual averaging)...")

# Get list of files
files = sorted([f"era5_data/{f}" for f in os.listdir("era5_data") if f.endswith("_natl.nc")])
print(f"  Found {len(files)} yearly files")

# Get dimensions from first file
print("  Reading dimensions...")
ds_sample = xr.open_dataset(files[0])
n_lat = len(ds_sample.latitude)
n_lon = len(ds_sample.longitude)
lat_vals = ds_sample.latitude.values
lon_vals = ds_sample.longitude.values
ds_sample.close()

# Initialize accumulators for each hour of the year
n_times = 365 * 24
u10_sum = np.zeros((n_times, n_lat, n_lon), dtype=np.float64)
v10_sum = np.zeros((n_times, n_lat, n_lon), dtype=np.float64)
count = np.zeros(n_times, dtype=np.int32)

print(f"  Output shape: ({n_times}, {n_lat}, {n_lon})")
print(f"  Memory for accumulators: ~{(u10_sum.nbytes + v10_sum.nbytes) / 1024 / 1024:.1f} MB")

# Process each file
for file_idx, file in enumerate(files):
    year = file.split('_')[-2]
    print(f"  Processing {year} ({file_idx+1}/{len(files)})...")
    
    ds = xr.open_dataset(file)
    
    # Get time info
    times = ds['valid_time'].values
    dayofyear = ds['valid_time'].dt.dayofyear.values
    hour = ds['valid_time'].dt.hour.values
    
    # Process each timestep
    for i in range(len(times)):
        doy = dayofyear[i]
        hr = hour[i]
        
        # Skip leap days (Feb 29)
        if doy >= 366:
            continue
        
        # Calculate index in output array
        time_idx = (doy - 1) * 24 + hr
        
        # Accumulate
        u10_sum[time_idx] += ds['u10'].isel(valid_time=i).values
        v10_sum[time_idx] += ds['v10'].isel(valid_time=i).values
        count[time_idx] += 1
    
    ds.close()
    
    # Print memory usage
    if (file_idx + 1) % 2 == 0:
        import psutil
        mem = psutil.virtual_memory()
        print(f"    Memory used: {mem.percent:.1f}% ({mem.used / 1024 / 1024 / 1024:.1f} GB / {mem.total / 1024 / 1024 / 1024:.1f} GB)")

print("  Computing averages...")
# Compute averages (avoid division by zero)
u10_clim = np.zeros_like(u10_sum, dtype=np.float32)
v10_clim = np.zeros_like(v10_sum, dtype=np.float32)

for i in range(n_times):
    if count[i] > 0:
        u10_clim[i] = u10_sum[i] / count[i]
        v10_clim[i] = v10_sum[i] / count[i]

print(f"  Averaged {count.min()} to {count.max()} samples per timestep")

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
ds_out['time'].attrs = {'long_name': 'time', 'standard_name': 'time'}
ds_out.attrs = {
    'title': 'ERA5 Climatological Average Year',
    'source': 'ERA5 reanalysis',
    'years_averaged': '1940-1945',
    'created': datetime.now().isoformat()
}

# Save
nc_out = "era5_typical_year_10m_wind_natlantic_manual.nc"
print(f"💾 Saving NetCDF: {nc_out}")
ds_out.to_netcdf(nc_out)

# Verify the file
print("  Verifying output...")
ds_verify = xr.open_dataset(nc_out)
print(f"  ✅ Time range: {ds_verify.time.values[0]} to {ds_verify.time.values[-1]}")
print(f"  ✅ Shape: {ds_verify.u10.shape}")
print(f"  ✅ U10 range: {float(ds_verify.u10.min()):.2f} to {float(ds_verify.u10.max()):.2f} m/s")
print(f"  ✅ V10 range: {float(ds_verify.v10.min()):.2f} to {float(ds_verify.v10.max()):.2f} m/s")
ds_verify.close()

# Convert to GRIB2
grib_out = "era5_typical_year_10m_wind_natlantic_manual.grb2"
print(f"🌀 Converting to GRIB2: {grib_out}")
try:
    subprocess.run(["cdo", "-f", "grb2", "copy", nc_out, grib_out], check=True)
    print("✅ Done!")
    print(f"\nOutput files:")
    print(f"  NetCDF: {nc_out}")
    print(f"  GRIB2: {grib_out}")
except subprocess.CalledProcessError as e:
    print(f"⚠️  CDO conversion failed: {e}")
    print(f"NetCDF file created: {nc_out}")
