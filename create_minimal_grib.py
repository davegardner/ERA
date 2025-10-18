#!/usr/bin/env python3
"""
Create a minimal GRIB2 file - just a few timesteps for testing.
Sometimes OpenCPN has issues with large time ranges.
"""

import xarray as xr
import subprocess
import os

print("Creating minimal GRIB2 file for testing...")

# Open the NetCDF file
nc_file = "era5_typical_year_6h_8x_1940-1940.nc"
ds = xr.open_dataset(nc_file)

# Take only first 7 days (28 timesteps at 6-hourly)
print("Extracting first 7 days (28 timesteps)...")
ds_small = ds.isel(time=slice(0, 28))

# Simplify to just wind speed components
ds_small = ds_small[['u10', 'v10']]

# Update attributes for GRIB compatibility
ds_small['u10'].attrs = {
    'long_name': '10 metre U wind component',
    'standard_name': 'eastward_wind',
    'units': 'm s-1'
}

ds_small['v10'].attrs = {
    'long_name': '10 metre V wind component', 
    'standard_name': 'northward_wind',
    'units': 'm s-1'
}

# Save small NetCDF
temp_nc = "temp_minimal.nc"
ds_small.to_netcdf(temp_nc)
ds_small.close()
ds.close()

# Convert to GRIB2
grib_file = "era5_minimal_test.grb2"
print(f"Converting to GRIB2: {grib_file}")

subprocess.run(
    ["cdo", "-f", "grb2", "copy", temp_nc, grib_file],
    check=True,
    timeout=60
)

os.remove(temp_nc)

# Get file size
size_kb = os.path.getsize(grib_file) / 1024
print(f"\n✅ Minimal test file created: {grib_file}")
print(f"   Size: {size_kb:.1f} KB")
print(f"   Timesteps: 28 (7 days, 6-hourly)")
print(f"   Grid: 35 x 60 points (2.0° spacing)")
print(f"\nTry this smaller file in OpenCPN first!")

# Show info
subprocess.run(["cdo", "sinfov", grib_file])
