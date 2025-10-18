#!/usr/bin/env python3
"""
Fast ERA5 climatology processor using vectorized operations.
Loads data in chunks to avoid slow timestep-by-timestep access.
"""

import xarray as xr
import numpy as np
import pandas as pd
import subprocess
import os
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='Fast ERA5 climatology processor')
    parser.add_argument('--temporal', type=int, default=6,
                        help='Temporal resolution in hours (1, 3, 6, 12, 24). Default: 6')
    parser.add_argument('--spatial', type=int, default=2,
                        help='Spatial coarsening factor (1, 2, 4, 8). Default: 2')
    parser.add_argument('--years', type=str, default='1940-1945',
                        help='Year range (e.g., "1940-1945"). Default: 1940-1945')
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Parse year range
    year_start, year_end = map(int, args.years.split('-'))
    years = list(range(year_start, year_end + 1))
    
    # Calculate output dimensions
    hours_per_day = 24 // args.temporal
    n_times = 365 * hours_per_day
    
    print(f"📊 Fast ERA5 Climatology Processor")
    print(f"=" * 70)
    print(f"Configuration:")
    print(f"  Temporal: {args.temporal}-hourly ({n_times} timesteps)")
    print(f"  Spatial: {args.spatial}x coarsening (~{0.25 * args.spatial:.2f}° grid)")
    print(f"  Years: {year_start}-{year_end} ({len(years)} years)")
    print()
    
    # Get list of files
    files = sorted([f"era5_data/era5_hourly_{y}_natl.nc" for y in years])
    files = [f for f in files if os.path.exists(f)]
    
    if not files:
        print(f"❌ No data files found")
        return
    
    print(f"  Found {len(files)} data files")
    
    # Get dimensions from first file
    print("  Reading dimensions...")
    ds_sample = xr.open_dataset(files[0])
    
    # Apply spatial coarsening
    if args.spatial > 1:
        ds_sample = ds_sample.coarsen(latitude=args.spatial, longitude=args.spatial, boundary='trim').mean()
    
    n_lat = len(ds_sample.latitude)
    n_lon = len(ds_sample.longitude)
    lat_vals = ds_sample.latitude.values
    lon_vals = ds_sample.longitude.values
    ds_sample.close()
    
    # Calculate memory
    mem_accum = (n_times * n_lat * n_lon * 8 * 2) / (1024**3)
    mem_output = (n_times * n_lat * n_lon * 4 * 2) / (1024**3)
    mem_total = mem_accum + mem_output + 1.0
    
    print(f"  Output shape: ({n_times}, {n_lat}, {n_lon})")
    print(f"  Memory estimate: {mem_total:.2f} GB")
    print()
    
    # Initialize accumulators
    u10_sum = np.zeros((n_times, n_lat, n_lon), dtype=np.float64)
    v10_sum = np.zeros((n_times, n_lat, n_lon), dtype=np.float64)
    count = np.zeros(n_times, dtype=np.int32)
    
    # Process each file
    for file_idx, file in enumerate(files):
        year = file.split('_')[-2]
        print(f"  Processing {year} ({file_idx+1}/{len(files)})...")
        
        ds = xr.open_dataset(file)
        
        # Apply spatial coarsening
        if args.spatial > 1:
            print(f"    Coarsening spatial grid...")
            ds = ds.coarsen(latitude=args.spatial, longitude=args.spatial, boundary='trim').mean()
        
        # Get time info as arrays
        print(f"    Computing time indices...")
        dayofyear = ds['valid_time'].dt.dayofyear.values
        hour = ds['valid_time'].dt.hour.values
        
        # Create mask for valid timesteps
        valid_mask = (dayofyear < 366) & (hour % args.temporal == 0)
        
        # Calculate output indices for all valid timesteps
        time_indices = (dayofyear - 1) * hours_per_day + (hour // args.temporal)
        
        # Load data arrays (this is the slow part, but only done once per file)
        print(f"    Loading wind data...")
        u10_data = ds['u10'].values
        v10_data = ds['v10'].values
        
        ds.close()
        
        # Vectorized accumulation
        print(f"    Accumulating {valid_mask.sum()} timesteps...")
        for i in np.where(valid_mask)[0]:
            idx = time_indices[i]
            u10_sum[idx] += u10_data[i]
            v10_sum[idx] += v10_data[i]
            count[idx] += 1
        
        print(f"    Done!")
    
    print()
    print("  Computing averages...")
    
    # Compute averages
    u10_clim = np.zeros_like(u10_sum, dtype=np.float32)
    v10_clim = np.zeros_like(v10_sum, dtype=np.float32)
    
    for i in range(n_times):
        if count[i] > 0:
            u10_clim[i] = u10_sum[i] / count[i]
            v10_clim[i] = v10_sum[i] / count[i]
    
    print(f"  Averaged {count.min()} to {count.max()} samples per timestep")
    
    # Create time coordinate
    print("  Creating output dataset...")
    typical_times = pd.date_range("2001-01-01", periods=n_times, freq=f"{args.temporal}h")
    
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
        'years_averaged': f'{year_start}-{year_end}',
        'region': 'North Atlantic (70N-0N, 100W-20E)',
        'temporal_resolution': f'{args.temporal}-hourly',
        'spatial_coarsening': f'{args.spatial}x',
        'grid_spacing': f'~{0.25 * args.spatial:.2f} degrees'
    }
    
    # Generate output filename
    suffix = f"{args.temporal}h_{args.spatial}x_{year_start}-{year_end}"
    nc_out = f"era5_typical_year_{suffix}.nc"
    grib_out = f"era5_typical_year_{suffix}.grb2"
    
    # Save NetCDF
    print(f"💾 Saving NetCDF: {nc_out}")
    ds_out.to_netcdf(nc_out)
    
    # Verify the file
    print("  Verifying output...")
    ds_verify = xr.open_dataset(nc_out)
    print(f"  ✅ Time range: {ds_verify.time.values[0]} to {ds_verify.time.values[-1]}")
    print(f"  ✅ Shape: {ds_verify.u10.shape}")
    print(f"  ✅ U10 range: {float(ds_verify.u10.min()):.2f} to {float(ds_verify.u10.max()):.2f} m/s")
    print(f"  ✅ V10 range: {float(ds_verify.v10.min()):.2f} to {float(ds_verify.v10.max()):.2f} m/s")
    print(f"  ✅ U10 mean: {float(ds_verify.u10.mean()):.2f} m/s")
    print(f"  ✅ V10 mean: {float(ds_verify.v10.mean()):.2f} m/s")
    
    # Get file size
    file_size = os.path.getsize(nc_out) / (1024**2)
    print(f"  ✅ File size: {file_size:.1f} MB")
    ds_verify.close()
    
    # Convert to GRIB2
    print(f"🌀 Converting to GRIB2: {grib_out}")
    try:
        result = subprocess.run(["cdo", "-f", "grb2", "copy", nc_out, grib_out], 
                               check=True, capture_output=True, text=True, timeout=120)
        print("✅ Done!")
        print()
        print(f"📦 Output files:")
        print(f"  NetCDF: {nc_out}")
        print(f"  GRIB2: {grib_out}")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  CDO conversion failed: {e.stderr}")
        print(f"📦 NetCDF file created: {nc_out}")
    except FileNotFoundError:
        print(f"⚠️  CDO not found - skipping GRIB2 conversion")
        print(f"📦 NetCDF file created: {nc_out}")
    except subprocess.TimeoutExpired:
        print(f"⚠️  CDO conversion timed out")
        print(f"📦 NetCDF file created: {nc_out}")
    
    print()
    print("=" * 70)
    print("✅ Processing complete!")
    print(f"Configuration: {args.temporal}-hourly, {args.spatial}x coarsening")
    print(f"Memory used: ~{mem_total:.1f} GB")
    print(f"Output: {n_times} timesteps, {n_lat}x{n_lon} grid")

if __name__ == "__main__":
    main()
