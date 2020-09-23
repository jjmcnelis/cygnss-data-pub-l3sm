# cygnss-data-pub-l3sm

This repo contains a simple procedure to render new, augmented netCDF files for the CYGNSS L3 Soil Moisture Product generated by CYGNSS investigators C. Chew and E. Small (2020). Their paper was published this year in *Remote Sensing*:

>Chew, C.; Small, E. Description of the UCAR/CU Soil Moisture Product. Remote Sens. 2020, 12, 1558. https://doi.org/10.3390/rs12101558

*If you're here to review  PODAAC's augmentations to the original netCDF files, browse the [*level3/*](level3/) directory for CDL header representations for the revised files generated by our script.*

## data

The source files (which are in pretty good shape to begin with, I should say) are located on a file server hosted by UCAR/COSMIC:

>https://data.cosmic.ucar.edu/gnss-r/soilMoisture/

The current handbook is copied into this repository at [ucar_cu_sm_handbook.pdf](ucar_cu_sm_handbook.pdf) (2020-09-23).

**Grab the latest copies of the netCDF files from UCAR/COSMIC using `wget`:**

```shell
wget -r -np -nH --cut-dirs=3 -R index.html https://data.cosmic.ucar.edu/gnss-r/soilMoisture/
```

Run that same command again and `wget` will attempt some rudimentary checks to reconcile the local copy of original netCDFs with available files in the UCAR/COSMIC directory.

**Decompress ALL downloaded gzipped netCDF files using the `find` and `tar` unix utilities:**

```shell
find level3/ -type f -name "*.gz" -exec gunzip {} \;
```

## revisions

### background

One inconvenient "gotcha" in netCDF is variable initialization -- we have to set the `_FillValue` and `datatype` for a variable when its initialized. (This is the case in every software implementation of netCDF model/format that I've ever used.) Some softwares manage that procedural aspect for the user. For instance, when you change a variable's data type using NCO, it's actually overwriting the old variable with a new one and copying the data/attributes over from the source variable.

The netCDF4 library is allocating space for the data array and prefilling it with the prescribed value whenever a user specifies a `_FillValue` for a new netCDF variable. It makes sense. It'd be awfully inefficient for netCDF to try to do all the dynamic memory management by itself. Every byte after the resized variable would need to be indexed again. Not feasible for large datasets. 

So that's the gist of why we felt it was necessary to write a dedicated script to modify these SM outputs that are already in great shape, for the most part. Some of our fixes have potential to be destructive, like updating the `_FillValue`s to something other than `NaN` as mentioned already.

### script

The modifier script `podaac_cygnss_sm_adapter.py` is written for Python 3. The only dependency is Python package `netCDF4`, maintained by Unidata. I prefer to install it in a conda environment from the `conda-forge` channel. (It has the most stable sources for geospatial tools I use alot; mostly GDAL dependencies GEOS and PROJ). You can try installing like this:

```shell
conda install -c conda-forge netCDF4
```

**usage:**

The script takes exactly one input argument, the path to a netCDF file structured like the production netCDF outputs produced by the CYGNSS investigators.

Here's an example that generated a revised copy of the first file in the series:

```shell
./podaac_cygnss_sm_adapter.py level3/2017/077/ucar_cu_cygnss_sm_v1_2017_077.nc
```

The new netCDF should be written to the same directory as the original, but with an underscore prefixing the original filename. Here's the header returned by `ncdump -h` for the revised file that was generated using the command shown above:

```shell
ncdump -h level3/2017/077/_ucar_cu_cygnss_sm_v1_2017_077.nc > docs/example_output_2017_077.cdl
```

Check the generic format for the revised netCDFs in the `ncdump` output [here](docs/example_output_2017_077.cdl).

### batch

To conveniently generate new netCDF files for ALL of the originals, apply our script to the results returned by `find`, like before:

```shell
find level3/ -type f -name "ucar_cu_cygnss_sm_v*.nc" -exec ./podaac_cygnss_sm_adapter.py {} \;
```

*Note that the `find` command is ignoring files that don't fit the wildcard pattern that excludes any revised netCDF files that already exist in the `level3/` directory (because they all begin with `_`).*

You may find it convenient to execute the script in other modes invoked from the shell. For instance, generate outputs for only one year's files:

```shell
find level3/2019/ -type f -name "ucar_cu_cygnss_sm_v*.nc" -exec ./podaac_cygnss_sm_adapter.py {} \;
```

*NOTE: I needed to handle some exceptions and re-process 2019 files due to date string representation that isn't consistent with the same string in the files for other years.*

If you make any modifications, should probably capture the stdout that's returned by the Python script with each successive execution in case a bug is introduced. Python sends exception messages and warnings to stdout, so you can just pipe all everything to a log file like this:

```shell
# Get a datetime stamp for the log filename using the unix `date` util:
TIMESTAMP = $(date +"%Y%m%dT%H%M%SZ")
# Call find like before and pipe output to the log file.
find level3/ -type f -name "ucar_cu_cygnss_sm_v*.nc" -exec ./podaac_cygnss_sm_adapter.py {} \; > "docs/${TIMESTAMP}.log"
```

## resources

I'm dumping headers with CDL extensions for ALL of the revised data files to (hopefully) make reviewing them a bit less tedious for Clara and Eric. Again, using the unix `find` command:

```shell
find level3/ -type f -name "_ucar_cu_cygnss_sm_v*.nc" -exec bash -c 'ncdump -h "${0}" > "${0/.nc/.cdl}"' {} \;
```

The files all have `.cdl` extension, and they're located adjacent to the original and revised files for which they document PODAAC's changes, for instance: [*level3/2017/077/_ucar_cu_cygnss_sm_v1_2017_077.cdl*](level3/2017/077/_ucar_cu_cygnss_sm_v1_2017_077.cdl)

## docs

handbook: [docs/ucar_cu_sm_handbook.pdf](docs/ucar_cu_sm_handbook.pdf)

>Excerpt for my reference, maybe cite later:
>"The value of the peak cross-correlation of each DDM (called `Pr,eff` in this document) is related to surface characteristics at the specular reflection point of the GNSS signal— including the roughness of the surface and the surface dielectric constant." (Section 1.5 CYGNSS Observables, *CYGNSS Soil Moisture Product User Handbook*)
