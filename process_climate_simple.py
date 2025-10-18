#!/usr/bin/env python3
"""
Simplified version: Process only 2 years (1940-1941) for faster testing.
Uses standard xarray operations with smaller dataset.
"""

import xarray as xr
import numpy as np
import pandas as pd
import subprocess

print("📊 Building climatological 'typical year' (2-year subset: 1940-1941)...")

# Open only first 2 years
print("  Loading data...")
ds_all = xr.open_mfdataset(
    ["era5_data/era5_hourly_1940_natl.nc", "era5_data/era5_hourly_1941_natl.nc"],
    combine='by_coords'
)

print(f"  Dataset shape: {ds_all.dims}")
print(f"  Memory estimate: ~{ds_all.nbytes / 1024 / 1024 / 1024:.1f} GB")

# Remove leap days
print("  Filtering leap days...")
dayofyear = ds_all['valid_time'].dt.dayofyear
hour = ds_all['valid_time'].dt.hour
valid = dayofyear < 366
ds_all = ds_all.sel(valid_time=valid)

# Add coordinates for grouping
ds_all = ds_all.assign_coords(dayofyear=dayofyear.sel(valid_time=valid))
ds_all = ds_all.assign_coords(hour=hour.sel(valid_time=valid))

print("  Grouping and averaging (this may take a few minutes)...")
# Group and average - use dask for lazy evaluation
ds_clim = ds_all.groupby(['dayofyear', 'hour']).mean('valid_time')

print("  Computing result...")
# Force computation
ds_clim = ds_clim.compute()

print("  Reconstructing time dimension...")
# Create output dataset with proper time coordinate
typical_times = pd.date_range("2001-01-01", periods=365*24, freq="h")

# Extract data in correct order
u10_data = []
v10_data = []

for day in range(1, 366):
    for hr in range(24):
        u10_data.append(ds_clim['u10'].sel(dayofyear=day, hour=hr).values)
        v10_data.append(ds_clim['v10'].sel(dayofyear=day, hour=hr).values)

u10_array = np.array(u10_data)
v10_array = np.array(v10_data)

# Create new dataset
ds_out = xr.Dataset(
    {
        'u10': (['time', 'latitude', 'longitude'], u10_array),
        'v10': (['time', 'latitude', 'longitude'], v10_array),
    },
    coords={
        'time': typical_times,
        'latitude': ds_clim['latitude'].values,
        'longitude': ds_clim['longitude'].values,
    }
)

# Add attributes
ds_out['u10'].attrs = {'long_name': '10 metre U wind component', 'units': 'm s**-1'}
ds_out['v10'].attrs = {'long_name': '10 metre V wind component', 'units': 'm s**-1'}
ds_out.attrs = {'title': 'ERA5 Climatological Average Year (1940-1941)', 'source': 'ERA5 reanalysis'}

# Save
nc_out = "era5_typical_year_10m_wind_natlantic_2yr.nc"
print(f"💾 Saving NetCDF: {nc_out}")
ds_out.to_netcdf(nc_out)

# Verify the file
print("  Verifying output...")
ds_verify = xr.open_dataset(nc_out)
print(f"  ✅ Time range: {ds_verify.time.values[0]} to {ds_verify.time.values[-1]}")
print(f"  ✅ Shape: {ds_verify.u10.shape}")
ds_verify.close()

# Convert to GRIB2
grib_out = "era5_typical_year_10m_wind_natlantic_2yr.grb2"
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
