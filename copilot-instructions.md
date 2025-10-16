# Copilot Instructions for ERA5 Climate Data Processing

## Project Overview
This is a climate data processing project that downloads ERA5 reanalysis data from Copernicus Climate Data Store (CDS) and creates climatological averages. The main workflow downloads historical hourly 10m wind data for the North Atlantic region (1940-1945) and builds a "typical year" by averaging each hour across all available years.

## Key Architecture & Data Flow

### Main Components
- **`down-climate.py`**: Single-file pipeline that handles data download → processing → format conversion
- **`era5_data/`**: Storage for downloaded yearly NetCDF files (`era5_hourly_{year}_natl.nc`)
- **Output files**: 
  - `era5_typical_year_10m_wind_natlantic.nc` (intermediate NetCDF)
  - `era5_typical_year_10m_wind_natlantic.grb2` (final GRIB2 for OpenCPN)

### Data Processing Pipeline
1. **Download Phase**: CDS API retrieval with geographic subsetting (North Atlantic: 70°N-0°N, 100°W-20°E)
2. **Climatology Phase**: Multi-file xarray processing with leap day removal and groupby operations
3. **Export Phase**: NetCDF → GRIB2 conversion using CDO (Climate Data Operators)

## Critical Dependencies & Setup

### Required External Tools
- **CDO (Climate Data Operators)**: Required for NetCDF to GRIB2 conversion
  ```bash
  # Installation varies by system
  sudo apt-get install cdo  # Ubuntu/Debian
  brew install cdo          # macOS
  ```

### Python Dependencies
Core scientific stack with climate-specific libraries:
- `cdsapi`: Copernicus Climate Data Store API client
- `xarray`: Multi-dimensional labeled data processing
- `numpy`, `pandas`: Standard scientific computing
- `netCDF4` (implicit dependency for xarray NetCDF support)

### Authentication Setup
CDS API requires credentials in `~/.cdsapirc`:
```ini
url: https://cds.climate.copernicus.eu/api/v2
key: {uid}:{api-key}
```

## Project-Specific Patterns

### Geographic Subsetting
All data requests use North Atlantic bounding box `[70, -100, 0, 20]` (N,W,S,E format).
This is hardcoded for marine weather routing applications.

### Temporal Processing Conventions
- **Leap day handling**: Always remove Feb 29 (`dayofyear < 366`) for consistent 365-day climatology
- **Time reconstruction**: Use `2001-01-01` as base for typical year (non-leap reference)
- **Grouping pattern**: `groupby([dayofyear, hour])` for climatological averaging

### File Naming Conventions
- Input: `era5_hourly_{year}_natl.nc` (year-specific downloads)
- Output: `era5_typical_year_10m_wind_natlantic.{nc,grb2}` (climatological products)

### Error Handling & Resumption
The script checks for existing files before downloading (`os.path.exists(outfile)`) to support resumable operations.

## Development Workflow

### Running the Pipeline
```bash
python3 down-climate.py
```
No command-line arguments - all configuration is embedded in the script.

### Modifying Temporal Coverage
Adjust the `years` list in `down-climate.py`. Current range: 1940-1945 (limited for development).

### Changing Geographic Extent
Modify the `area` variable: `[North, West, South, East]` in decimal degrees.

### Adding Variables
Extend the `variables` list with ERA5 parameter names (e.g., `'mean_sea_level_pressure'`).

## Integration Points

### CDS API Integration
- Requires active Copernicus account and API key
- Large downloads may be queued by CDS servers
- Uses standard ERA5 single-level product requests

### CDO Integration
- Subprocess call to system-installed CDO
- GRIB2 output formatted for marine navigation software (OpenCPN)
- Error handling relies on CDO exit codes

### Xarray Multi-file Processing
Uses `open_mfdataset()` with `combine='by_coords'` for automatic file concatenation.
Assumes consistent coordinate systems across yearly files.

## Environment Recommendations

- Python 3.7+ environment (e.g., virtualenv, conda)
- Sufficient disk space for multi-year ERA5 data (several GB)
- Reliable internet connection for data downloads
- Unix-like OS recommended for CDO compatibility (Linux, macOS)
- Optional: Jupyter Notebook for interactive data exploration
- Version control (e.g., Git) for tracking changes to `down-climate.py`
- Regularly update dependencies to latest stable versions for compatibility and security

## Environment Setup
1. Create a virtual environment:
    ```bash
    python3 -m venv env
    source env/bin/activate
    ```
2. Install Python dependencies:

    ```bash
    pip install cdsapi xarray numpy pandas netCDF4
    ```
3. Install CDO as per your OS instructions above.   
4. Configure CDS API credentials in `~/.cdsapirc`.
5. Run the pipeline:
    ```bash
    python3 down-climate.py
    ``` 
## Testing & Validation
- Validate output files using tools like `ncdump` (NetCDF) and `w
grib` (GRIB2).
- Visualize data with Panoply or Python plotting libraries (Matplotlib, Cartopy).
- Cross-check climatological averages against known ERA5 statistics for the region.
- Implement unit tests for key functions in `down-climate.py` if extending functionality.
- Use logging to capture runtime information and errors for debugging.
- Regularly back up downloaded data and output files to avoid data loss.
- Document any changes to the script or workflow in a project README or changelog.
- Engage with the Copernicus user community for support and best practices.
- Monitor CDS service status for any outages or maintenance that may affect data access.
- Consider using Docker for containerized environments to ensure consistency across different systems.
- Schedule periodic runs of the pipeline to update climatological data as new ERA5 data becomes available.
- Review and comply with Copernicus data usage policies and attribution requirements.
- Use version control (e.g., Git) to manage changes to the script and track history.
- Regularly update dependencies to latest stable versions for compatibility and security.
- Consider using Docker for containerized environments to ensure consistency across different systems.
- Schedule periodic runs of the pipeline to update climatological data as new ERA5 data becomes available.
- Review and comply with Copernicus data usage policies and attribution requirements.
- Use version control (e.g., Git) to manage changes to the script and track history.
- Regularly update dependencies to latest stable versions for compatibility and security.
- Consider using Docker for containerized environments to ensure consistency across different systems.
- Schedule periodic runs of the pipeline to update climatological data as new ERA5 data becomes available.
- Review and comply with Copernicus data usage policies and attribution requirements.