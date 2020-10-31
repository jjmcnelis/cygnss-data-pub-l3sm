#!/bin/bash

# Executes the steps outlined in the README in a sequence to batch process.
T=$(date +"%Y%m%dT%H%M%SZ")

echo "# [1/4] Grab the latest copies of the netCDF files from UCAR/COSMIC using 'wget'. "
#wget -r -np -nH --cut-dirs=3 -R index.html https://data.cosmic.ucar.edu/gnss-r/soilMoisture/

echo "# [2/4] Decompress ALL downloaded gzipped netCDF files using the 'find' and 'tar' unix utils. "
find level3/ -type f -name "*.gz" -exec gunzip {} \;

echo "# [3/4] Call find and loop the found netCDFs, piping output to a log file. "
find level3/ -type f -name "ucar_cu_cygnss_sm_v*.nc" -exec ./podaac_cygnss_sm_adapter.py {} \;

echo "# [4/4] Dump CDL headers for Clara's and Eric's reference. "
find level3/ -type f -name "_ucar_cu_cygnss_sm_v*.nc" -exec bash -c 'ncdump -h "${0}" > "${0/.nc/.cdl}" ' {} \;
