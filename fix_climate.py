#!/usr/bin/env python3
import xarray as xr
import numpy as np
import pandas as pd
import subprocess

print("📊 Building climatological 'typical year'...")

# Open all files
ds_all = xr.open_mfdataset("era5_data/era5_hourly_*_natl.nc", combine='by_coords')

# Remove leap days
dayofyear = ds_all['valid_time'].dt.dayofyear
hour = ds_all['valid_time'].dt.hour
valid = dayofyear < 366
ds_all = ds_all.sel(valid_time=valid)

# Add coordinates for grouping
ds_all = ds_all.assign_coords(dayofyear=dayofyear.sel(valid_time=valid))
ds_all = ds_all.assign_coords(hour=hour.sel(valid_time=valid))

print("  Grouping and averaging...")
# Group and average
ds_clim = ds_all.groupby(['dayofyear', 'hour']).mean('valid_time')

print("  Reconstructing time dimension...")
# Create output dataset manually
typical_times = pd.date_range("2001-01-01", periods=365*24, freq="h")

# Extract data arrays and create new dataset
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
ds_out['u10'].attrs = ds_all['u10'].attrs
ds_out['v10'].attrs = ds_all['v10'].attrs
ds_out.attrs = ds_all.attrs

# Save
nc_out = "era5_typical_year_10m_wind_natlantic.nc"
print(f"💾 Saving NetCDF: {nc_out}")
ds_out.to_netcdf(nc_out)

# Convert to GRIB2
grib_out = "era5_typical_year_10m_wind_natlantic.grb2"
print(f"🌀 Converting to GRIB2: {grib_out}")
subprocess.run(["cdo", "-f", "grb2", "copy", nc_out, grib_out], check=True)

print("✅ Done!")
print(f"Output GRIB2: {grib_out}")
