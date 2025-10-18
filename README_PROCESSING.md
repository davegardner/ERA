# ERA5 Climatology Processing - Solutions

## Problem Summary

The original `down-climate.py` script encounters issues when processing 30GB of ERA5 data:
- Memory-intensive groupby operations on large datasets
- Time coordinate corruption after multi-index flattening
- Long processing times (>10 minutes)

## Three Alternative Solutions

### 1. **process_climate_manual.py** (RECOMMENDED)
**Best for: Production use with all 6 years of data**

**Approach:** Manual averaging without xarray groupby
- Processes one file at a time
- Uses numpy accumulators (float64 for precision)
- Memory efficient: ~200MB for accumulators
- Avoids problematic groupby operations

**Pros:**
- Most memory efficient
- Predictable memory usage
- Works with any number of years
- No xarray groupby issues

**Cons:**
- Slower (processes each file sequentially)
- More code complexity

**Usage:**
```bash
python3 process_climate_manual.py
```

**Output:**
- `era5_typical_year_10m_wind_natlantic_manual.nc`
- `era5_typical_year_10m_wind_natlantic_manual.grb2`

---

### 2. **process_climate_simple.py**
**Best for: Quick testing with subset of data**

**Approach:** Standard xarray operations on 2-year subset (1940-1941)
- Uses only first 2 years (~10GB instead of 30GB)
- Standard groupby with dask
- Faster for testing

**Pros:**
- Faster processing (~5 minutes)
- Good for testing workflow
- Uses standard xarray patterns

**Cons:**
- Only 2 years of data (less representative climatology)
- Still uses groupby (may have issues)
- Requires ~10GB memory

**Usage:**
```bash
python3 process_climate_simple.py
```

**Output:**
- `era5_typical_year_10m_wind_natlantic_2yr.nc`
- `era5_typical_year_10m_wind_natlantic_2yr.grb2`

---

### 3. **process_climate_chunked.py**
**Best for: Day-by-day processing**

**Approach:** Process one day/hour at a time across all years
- Opens each file multiple times (once per day/hour combination)
- Very memory efficient per iteration
- Good for debugging specific days

**Pros:**
- Minimal memory per iteration
- Easy to debug specific time periods
- Can resume if interrupted

**Cons:**
- Slowest approach (many file opens)
- I/O intensive
- May take 30+ minutes

**Usage:**
```bash
python3 process_climate_chunked.py
```

**Output:**
- `era5_typical_year_10m_wind_natlantic_chunked.nc`
- `era5_typical_year_10m_wind_natlantic_chunked.grb2`

---

## Monitoring Memory Usage

While processing, monitor memory in another terminal:

```bash
watch -n 5 'free -h && echo "---" && ps aux | grep python | grep -v grep'
```

Or use the provided script:

```bash
./monitor_memory.sh
```

---

## Current System Status

✅ **Downloaded data:** 6 years (1940-1945), ~30GB in `era5_data/`
✅ **Dependencies installed:** cdsapi, xarray, netCDF4, dask, numpy, pandas, CDO
✅ **CDS credentials:** Configured in `~/.cdsapirc`

**System resources:**
- RAM: 15.3 GB total, ~14 GB available
- Disk: 77 GB total, 15 GB free (63 GB used by downloaded data)

---

## Recommended Workflow

### For Production (All 6 Years):
```bash
# Use manual version - most reliable
python3 process_climate_manual.py

# Monitor progress (in another terminal)
tail -f manual_output.log
```

### For Quick Testing:
```bash
# Use 2-year version for faster results
python3 process_climate_simple.py
```

### If Memory Issues Persist:
```bash
# Use chunked version - slowest but most memory-safe
python3 process_climate_chunked.py
```

---

## Verifying Output

After processing completes, verify the files:

```bash
# Check file sizes
ls -lh era5_typical_year_10m_wind_natlantic_*.nc
ls -lh era5_typical_year_10m_wind_natlantic_*.grb2

# Verify NetCDF structure
python3 -c "
import xarray as xr
ds = xr.open_dataset('era5_typical_year_10m_wind_natlantic_manual.nc')
print('Time range:', ds.time.values[0], 'to', ds.time.values[-1])
print('Shape:', ds.u10.shape)
print('U10 range:', float(ds.u10.min()), 'to', float(ds.u10.max()), 'm/s')
print('V10 range:', float(ds.v10.min()), 'to', float(ds.v10.max()), 'm/s')
"

# Verify GRIB2 (if CDO conversion succeeded)
cdo info era5_typical_year_10m_wind_natlantic_manual.grb2
```

---

## Troubleshooting

### Script times out or gets killed
- System may be running out of memory
- Try the chunked version: `process_climate_chunked.py`
- Or reduce to 2 years: `process_climate_simple.py`

### CDO conversion fails
- NetCDF file is still usable
- Try manual conversion: `cdo -f grb2 copy input.nc output.grb2`
- Check CDO version: `cdo --version`

### Time coordinate issues
- The manual version avoids this by creating time coordinate directly
- Don't use the original `down-climate.py` - it has known issues

---

## Next Steps

1. Choose appropriate script based on your needs
2. Run the script (may take 10-30 minutes depending on version)
3. Verify output files
4. Use GRIB2 file in OpenCPN for marine navigation

---

## File Descriptions

- `down-climate.py` - Original script (has issues, don't use)
- `process_climate_manual.py` - **RECOMMENDED** - Manual averaging, all years
- `process_climate_simple.py` - Quick test version, 2 years only
- `process_climate_chunked.py` - Day-by-day processing, very memory-safe
- `fix_climate.py` - Earlier attempt (superseded by above scripts)
- `monitor_memory.sh` - Memory monitoring utility
