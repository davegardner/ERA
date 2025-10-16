# Cell 2: Setup CDS API credentials
import os
from google.colab import files

# Option 1: Upload your .cdsapirc file
print("Upload your .cdsapirc file (contains your CDS API key)")
uploaded = files.upload()

# Move to home directory
if '.cdsapirc' in uploaded:
    !mv .cdsapirc ~/.cdsapirc
    print("CDS API credentials configured")
else:
    # Option 2: Manual entry
    print("Create CDS API credentials manually:")
    print("1. Go to https://cds.climate.copernicus.eu/api-how-to")
    print("2. Get your UID and API key")

    # Create credentials file manually if needed
    cds_uid = input("Enter your CDS UID: ")
    cds_key = input("Enter your CDS API key: ")

    cdsapirc_content = f"""url: https://cds.climate.copernicus.eu/api/v2
key: {cds_uid}:{cds_key}"""

    with open(os.path.expanduser('~/.cdsapirc'), 'w') as f:
        f.write(cdsapirc_content)
    print("CDS API credentials created")
    