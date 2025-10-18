# ERA5 Resolution Configuration Guide

## Quick Start

Use the configurable processor to adjust memory requirements:

```bash
# Recommended for current 15GB RAM
python3 process_climate_configurable.py --preset coastal

# For offshore routing (very fast)
python3 process_climate_configurable.py --preset offshore

# Maximum detail (requires 32GB RAM)
python3 process_climate_configurable.py --preset maximum
```

## Resolution Options

### Temporal Resolution

Controls how many timesteps per day are in the output:

| Option | Timesteps/Year | Memory Impact | Use Case |
|--------|----------------|---------------|----------|
| `--temporal 1` (hourly) | 8,760 | 27.5 GB | Research, diurnal patterns |
| `--temporal 3` (3-hourly) | 2,920 | 9.8 GB | **Coastal navigation** ⭐ |
| `--temporal 6` (6-hourly) | 1,460 | 5.4 GB | **Offshore routing** ⭐ |
| `--temporal 12` (12-hourly) | 730 | 3.2 GB | Strategic planning |
| `--temporal 24` (daily) | 365 | 2.1 GB | Long-term climatology |

### Spatial Resolution

Controls grid coarsening (1 = no coarsening):

| Option | Grid Spacing | Points | Memory Impact | Use Case |
|--------|--------------|--------|---------------|----------|
| `--spatial 1` | 0.25° (~28 km) | 135,161 | Baseline | **Coastal detail** ⭐ |
| `--spatial 2` | 0.5° (~56 km) | 33,981 | 75% reduction | **Offshore** ⭐ |
| `--spatial 4` | 1.0° (~111 km) | 8,591 | 94% reduction | Large-scale patterns |
| `--spatial 8` | 2.0° (~222 km) | 2,196 | 98% reduction | Overview only |

## Preset Configurations

### Coastal Navigation (Current 15GB RAM)
```bash
python3 process_climate_configurable.py --preset coastal
# Equivalent to: --temporal 3 --spatial 1
```
- **Memory:** 9.8 GB ✅ Fits in 15GB
- **Processing:** ~5 minutes for 6 years
- **Output:** 3 GB NetCDF
- **Resolution:** 3-hourly, 0.25° grid
- **Best for:** Coastal sailing, keeps spatial detail

### Offshore Routing
```bash
python3 process_climate_configurable.py --preset offshore
# Equivalent to: --temporal 6 --spatial 2
```
- **Memory:** 2.1 GB ✅ Very light
- **Processing:** ~2.5 minutes for 6 years
- **Output:** 378 MB NetCDF
- **Resolution:** 6-hourly, 0.5° grid
- **Best for:** Ocean passages, weather routing

### Planning/Overview
```bash
python3 process_climate_configurable.py --preset planning
# Equivalent to: --temporal 24 --spatial 4
```
- **Memory:** 1.1 GB ✅ Minimal
- **Processing:** <1 minute for 6 years
- **Output:** 24 MB NetCDF
- **Resolution:** Daily, 1.0° grid
- **Best for:** Long-term planning, climatology

### Maximum Detail (Requires 32GB RAM)
```bash
python3 process_climate_configurable.py --preset maximum
# Equivalent to: --temporal 1 --spatial 1
```
- **Memory:** 27.5 GB ⚠️ Needs 32GB RAM
- **Processing:** ~15 minutes for 6 years
- **Output:** 9 GB NetCDF
- **Resolution:** Hourly, 0.25° grid
- **Best for:** Research, maximum detail

## Custom Configurations

### Example: 3-hourly with coarser grid
```bash
python3 process_climate_configurable.py --temporal 3 --spatial 2
# Memory: ~2.5 GB, very fast
```

### Example: Process different year range
```bash
python3 process_climate_configurable.py --preset coastal --years 1940-1960
# Process 20 years instead of 6
```

### Example: Custom output filename
```bash
python3 process_climate_configurable.py --preset offshore --output my_climatology
# Creates: my_climatology.nc and my_climatology.grb2
```

## Memory Requirements Summary

| Configuration | Memory | 15GB RAM | 32GB RAM | Processing Time (6yr) |
|---------------|--------|----------|----------|-----------------------|
| Hourly, 0.25° | 27.5 GB | ❌ | ✅ | 15 min |
| 3-hourly, 0.25° | 9.8 GB | ✅ | ✅ | 5 min |
| 6-hourly, 0.5° | 2.1 GB | ✅ | ✅ | 2.5 min |
| Daily, 1.0° | 1.1 GB | ✅ | ✅ | <1 min |

## Scaling with Years

**Key insight:** Memory usage is independent of the number of input years!

| Years | Disk Space | Processing Time (3-hourly) |
|-------|------------|----------------------------|
| 6 | 30 GB | 5 min |
| 10 | 50 GB | 8 min |
| 20 | 100 GB | 17 min |
| 30 | 150 GB | 25 min |

Memory stays constant at 9.8 GB for 3-hourly, 0.25° regardless of year count.

## Trade-offs

### Temporal Resolution
- **Hourly:** Captures diurnal wind patterns (sea breeze, land breeze)
- **3-hourly:** Standard synoptic interval, still shows daily cycles
- **6-hourly:** Standard model output, sufficient for routing
- **Daily:** Misses wind shifts, only for long-term planning

### Spatial Resolution
- **0.25°:** Shows coastal effects, topographic influences
- **0.5°:** Still captures major features, good for offshore
- **1.0°:** Large-scale patterns only, loses coastal detail
- **2.0°:** Overview only, too coarse for navigation

## Recommendations by RAM

### Current 15GB RAM
🥇 **Best:** `--preset coastal` (3-hourly, 0.25°)
- Fits comfortably in RAM
- Keeps full spatial detail
- 3x faster than hourly
- Good for all navigation types

🥈 **Alternative:** `--preset offshore` (6-hourly, 0.5°)
- Very fast and light
- Perfect for ocean passages
- Sacrifice some coastal detail

### Upgraded 32GB RAM
🥇 **Best:** `--preset maximum` (hourly, 0.25°)
- No compromises
- Maximum detail
- Worth it if you need hourly data

🥈 **Alternative:** `--preset coastal` (3-hourly, 0.25°)
- Still faster processing
- Leaves RAM headroom
- Probably sufficient for most uses

## Technical Details

### How Temporal Reduction Works
The script only accumulates timesteps that match the desired interval:
```python
if hour % temporal_resolution == 0:
    accumulate_data()
```

### How Spatial Coarsening Works
Uses xarray's `coarsen()` to average neighboring grid points:
```python
ds = ds.coarsen(latitude=factor, longitude=factor, boundary='trim').mean()
```

### Memory Formula
```
Memory (GB) = (timesteps × lat_points × lon_points × 8 bytes × 2 vars) / 1024³
            + (timesteps × lat_points × lon_points × 4 bytes × 2 vars) / 1024³
            + 1 GB overhead
```

Where:
- First term: accumulators (float64)
- Second term: output arrays (float32)
- 2 vars: u10 and v10 wind components

## Troubleshooting

### Out of Memory
- Use `--preset offshore` or `--preset planning`
- Reduce `--temporal` value (increase hours)
- Increase `--spatial` value (coarsen grid)

### Processing Too Slow
- Reduce temporal resolution: `--temporal 6` or `--temporal 24`
- Coarsen spatial grid: `--spatial 2` or `--spatial 4`

### Output File Too Large
- Same solutions as "Processing Too Slow"
- File size scales with timesteps × grid points

### Need More Years
- Memory usage doesn't increase with more years!
- Only disk space and processing time increase
- Use `--years 1940-1960` for 20 years
