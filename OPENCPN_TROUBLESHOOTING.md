# OpenCPN GRIB Troubleshooting Guide

## Problem: "Invalid GRIB" Error in OpenCPN

Several test files have been created to help diagnose the issue:

## Test Files Available

### 1. Minimal Test File (GRIB2) - 469 KB
**File:** `era5_minimal_test.grb2`
- 7 days of data (28 timesteps)
- 6-hourly intervals
- 2.0° grid (35 × 60 points)
- **Try this first** - smallest file for testing

### 2. Minimal Test File (GRIB1) - 235 KB  
**File:** `era5_minimal_test.grb`
- Same as above but GRIB1 format
- Some older OpenCPN versions prefer GRIB1
- Half the file size

### 3. Full Year (GRIB2 with metadata) - 24 MB
**File:** `era5_typical_year_6h_8x_1940-1940_opencpn.grb2`
- Full 365 days
- Enhanced metadata for compatibility
- 2.0° grid

### 4. Original Full Year (GRIB2) - 24 MB
**File:** `era5_typical_year_6h_8x_1940-1940.grb2`
- Full 365 days
- Standard conversion
- 2.0° grid

## Common OpenCPN GRIB Issues

### Issue 1: File Size
- **Problem:** OpenCPN may have memory limits
- **Solution:** Try the minimal test files first (< 500 KB)
- **Test:** If minimal works, the issue is file size

### Issue 2: GRIB Format Version
- **Problem:** Some OpenCPN versions only support GRIB1
- **Solution:** Try the `.grb` file (GRIB1) instead of `.grb2` (GRIB2)
- **Note:** GRIB1 is older but more widely supported

### Issue 3: Parameter Codes
- **Problem:** OpenCPN expects specific wind parameter codes
- **Current status:** Files show "u" and "v" parameters
- **Expected:** Should be recognized as wind components
- **Check:** Open GRIB in a text editor - should see wind-related metadata

### Issue 4: Time Range
- **Problem:** Very long time ranges (365 days) may cause issues
- **Solution:** Use minimal test file (7 days only)
- **Workaround:** Split into monthly files if needed

### Issue 5: Grid Type
- **Problem:** OpenCPN may not support all grid types
- **Current:** Regular lat/lon grid (should be compatible)
- **Status:** This should NOT be the issue

### Issue 6: Missing Metadata
- **Problem:** GRIB files need proper parameter identification
- **Status:** CDO conversion may not preserve all metadata
- **Alternative:** Need to use specialized GRIB writing tools

## Diagnostic Steps

### Step 1: Try Minimal GRIB2
```
Download: era5_minimal_test.grb2 (469 KB)
Load in OpenCPN
```
- ✅ **If it works:** Issue is file size - need to split data
- ❌ **If it fails:** Try Step 2

### Step 2: Try Minimal GRIB1
```
Download: era5_minimal_test.grb (235 KB)
Load in OpenCPN
```
- ✅ **If it works:** OpenCPN needs GRIB1 format
- ❌ **If it fails:** Try Step 3

### Step 3: Check OpenCPN Version
- OpenCPN 5.x generally supports GRIB2
- OpenCPN 4.x may prefer GRIB1
- Check: Help → About in OpenCPN

### Step 4: Check OpenCPN GRIB Plugin
- Ensure GRIB plugin is installed and enabled
- Check: Tools → Plugins → GRIB
- May need to enable "ClimaData" or similar

### Step 5: Try Sample GRIB from NOAA
Download a known-good GRIB from:
- https://nomads.ncep.noaa.gov/
- If NOAA GRIB works but ours doesn't, it's a format issue

## Possible Solutions

### Solution A: Convert to GRIB1 (if GRIB2 fails)
All files can be converted to GRIB1:
```bash
cdo -f grb copy input.grb2 output.grb
```

### Solution B: Split into Smaller Files
Create monthly files instead of full year:
- January: 124 timesteps
- February: 112 timesteps
- etc.

### Solution C: Use NetCDF Instead
OpenCPN may support NetCDF format:
- File: `era5_typical_year_6h_8x_1940-1940.nc`
- Check if OpenCPN can load .nc files

### Solution D: Use Different Tool
If OpenCPN won't work, alternatives:
- **qtVlm:** Marine navigation software with GRIB support
- **XyGrib:** Dedicated GRIB viewer
- **Panoply:** Scientific data viewer

## What to Report Back

Please test the files in this order and report:

1. **Minimal GRIB2** (era5_minimal_test.grb2) - Works? Yes/No
2. **Minimal GRIB1** (era5_minimal_test.grb) - Works? Yes/No
3. **OpenCPN Version** - What version are you running?
4. **Error Message** - Exact text of any error
5. **GRIB Plugin Status** - Installed and enabled?

This will help determine the exact issue and solution.

## Technical Details

### Current GRIB Structure
```
Format: GRIB2
Parameters: u (eastward wind), v (northward wind)
Grid: Regular lat/lon, 2.0° spacing
Levels: Surface (10m height)
Time: 6-hourly intervals
Reference: 2001-01-01 (climatology reference year)
```

### What OpenCPN Expects
- Wind components at 10m height
- Regular lat/lon grid
- Standard GRIB1 or GRIB2 format
- Reasonable file size (< 100 MB typically)
- Proper parameter codes (33=u, 34=v for GRIB1)

## Next Steps

1. Download and test `era5_minimal_test.grb2` (469 KB)
2. If that fails, try `era5_minimal_test.grb` (235 KB)
3. Report back which format works (if any)
4. We can then create the full dataset in the working format
