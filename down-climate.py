    #!/usr/bin/env python3
"""
Build a climatological 'average year' of ERA5 10m winds (hourly resolution)
for the North Atlantic region only.

Each hour of the year is averaged across all available years (1940–present).
Output: 'era5_typical_year_10m_wind_natlantic.grb2'
"""

import cdsapi
import os
import xarray as xr
import numpy as np
import pandas as pd
import subprocess

# Initialize the CDS API client
c = cdsapi.Client()

# Variables and temporal coverage
variables = ['10m_u_component_of_wind', '10m_v_component_of_wind']
years = list(range(1940, 1946))  # adjust upper year as needed
months = [f"{m:02d}" for m in range(1, 13)]
days = [f"{d:02d}" for d in range(1, 32)]
hours = [f"{h:02d}:00" for h in range(24)]

# North Atlantic bounding box: [N, W, S, E]
#   covers 70°N–0°N, 100°W–20°E
area = [70, -100, 0, 20]

# Folder for downloaded yearly data
os.makedirs("era5_data", exist_ok=True)

# 1️⃣ Download ERA5 hourly data (subset to North Atlantic)
for year in years:
    outfile = f"era5_data/era5_hourly_{year}_natl.nc"
    if os.path.exists(outfile):
        print(f"✅ {outfile} exists, skipping.")
        continue

    print(f"⬇️ Downloading ERA5 hourly data for {year} (North Atlantic)...")
    c.retrieve(
        'reanalysis-era5-single-levels',
        {
            'product_type': 'reanalysis',
            'variable': variables,
            'year': str(year),
            'month': months,
            'day': days,
            'time': hours,
            'area': area,     # North, West, South, East
            'format': 'netcdf'
        },
        outfile,
    )

# 2️⃣ Build the multi-year climatological 'average year'
print("📊 Building climatological 'typical year'...")

ds_all = xr.open_mfdataset("era5_data/era5_hourly_*_natl.nc", combine='by_coords')

# Remove leap days to make a 365-day calendar
ds_all = ds_all.assign_coords(dayofyear=ds_all['valid_time'].dt.dayofyear)
ds_all = ds_all.assign_coords(hour=ds_all['valid_time'].dt.hour)
valid = ds_all['dayofyear'] < 366
ds_all = ds_all.sel(valid_time=valid)

# Group by (day of year, hour) and average across years
print("  Grouping and averaging...")
ds_clim = ds_all.groupby(['dayofyear', 'hour']).mean('valid_time')

# Create a simple integer index for time
print("  Creating time coordinate...")
n_times = 365 * 24
time_index = np.arange(n_times)

# Flatten the multi-index result
ds_clim = ds_clim.stack(time=('dayofyear', 'hour'))
ds_clim = ds_clim.sortby('time')

# Replace the multi-index with a simple integer index
ds_clim = ds_clim.reset_index('time', drop=True)
ds_clim = ds_clim.assign_coords(time=time_index)

# Add time attributes for CF compliance
ds_clim['time'].attrs['units'] = 'hours since 2001-01-01 00:00:00'
ds_clim['time'].attrs['calendar'] = 'standard'
ds_clim['time'].attrs['long_name'] = 'time'

# Ensure proper coordinate order for CDO
ds_clim = ds_clim.transpose('time', 'latitude', 'longitude')

# 3️⃣ Save to NetCDF
nc_out = "era5_typical_year_10m_wind_natlantic.nc"
print(f"💾 Saving NetCDF: {nc_out}")
ds_clim.to_netcdf(nc_out)

# 4️⃣ Convert to GRIB2 (for OpenCPN)
grib_out = "era5_typical_year_10m_wind_natlantic.grb2"
print(f"🌀 Converting to GRIB2: {grib_out}")
subprocess.run(["cdo", "-f", "grb2", "copy", nc_out, grib_out], check=True)

print("✅ Done!")
print(f"Output GRIB2: {grib_out}")
