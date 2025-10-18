#!/usr/bin/env python3
"""
Create a properly formatted GRIB2 file with correct parameter codes for OpenCPN.
"""

import xarray as xr
import subprocess
import os

print("Creating OpenCPN-compatible GRIB2 file...")

# Open the NetCDF file
nc_file = "era5_typical_year_6h_8x_1940-1940.nc"
grib_file = "era5_typical_year_6h_8x_1940-1940_opencpn.grb2"

print(f"Reading: {nc_file}")
ds = xr.open_dataset(nc_file)

# Add proper CF metadata for GRIB2 conversion
ds['u10'].attrs.update({
    'long_name': '10 metre U wind component',
    'standard_name': 'eastward_wind',
    'units': 'm s-1',
    'GRIB_paramId': '165',
    'GRIB_shortName': '10u',
    'GRIB_name': 'U component of wind',
    'GRIB_cfName': 'eastward_wind',
    'GRIB_cfVarName': 'u10',
    'GRIB_dataType': 'fc',
    'GRIB_missingValue': 9999,
    'GRIB_numberOfPoints': len(ds.latitude) * len(ds.longitude),
    'GRIB_typeOfLevel': 'heightAboveGround',
    'GRIB_stepUnits': 1,
    'GRIB_stepType': 'instant',
    'GRIB_gridType': 'regular_ll',
    'GRIB_NV': 0,
    'GRIB_Nx': len(ds.longitude),
    'GRIB_Ny': len(ds.latitude),
})

ds['v10'].attrs.update({
    'long_name': '10 metre V wind component',
    'standard_name': 'northward_wind',
    'units': 'm s-1',
    'GRIB_paramId': '166',
    'GRIB_shortName': '10v',
    'GRIB_name': 'V component of wind',
    'GRIB_cfName': 'northward_wind',
    'GRIB_cfVarName': 'v10',
    'GRIB_dataType': 'fc',
    'GRIB_missingValue': 9999,
    'GRIB_numberOfPoints': len(ds.latitude) * len(ds.longitude),
    'GRIB_typeOfLevel': 'heightAboveGround',
    'GRIB_stepUnits': 1,
    'GRIB_stepType': 'instant',
    'GRIB_gridType': 'regular_ll',
    'GRIB_NV': 0,
    'GRIB_Nx': len(ds.longitude),
    'GRIB_Ny': len(ds.latitude),
})

# Save updated NetCDF
temp_nc = "temp_with_metadata.nc"
print(f"Saving temporary NetCDF with proper metadata...")
ds.to_netcdf(temp_nc)
ds.close()

# Convert to GRIB2 with proper encoding
print(f"Converting to GRIB2: {grib_file}")
try:
    # Try with setgridtype to ensure proper grid encoding
    result = subprocess.run(
        ["cdo", "-f", "grb2", "setgridtype,regular", temp_nc, grib_file],
        check=True,
        capture_output=True,
        text=True,
        timeout=60
    )
    print("✅ GRIB2 created successfully")
except subprocess.CalledProcessError as e:
    print(f"⚠️  First attempt failed, trying simpler conversion...")
    # Fallback to simple conversion
    subprocess.run(
        ["cdo", "-f", "grb2", "copy", temp_nc, grib_file],
        check=True,
        timeout=60
    )
    print("✅ GRIB2 created with fallback method")

# Clean up temp file
os.remove(temp_nc)

# Verify the output
print("\nVerifying GRIB2 file...")
result = subprocess.run(
    ["cdo", "sinfov", grib_file],
    capture_output=True,
    text=True
)
print(result.stdout[:500])

# Get file size
size_mb = os.path.getsize(grib_file) / (1024**2)
print(f"\n✅ File created: {grib_file}")
print(f"   Size: {size_mb:.1f} MB")
print(f"\nThis file should work in OpenCPN!")
