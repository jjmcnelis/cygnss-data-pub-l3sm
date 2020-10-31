#!/usr/bin/env python3
"""
# CYGNSS Level 3 Soil Moisture from UCAR/CU 
# Chew and Small, 2020
#
# This script demos an approach for producing a revised version of a netCDF 
# that conforms to a known structure using an efficient process that leverages
# Unidata's excellent Python interface to the netCDF C library.
#  
# netCDF is and its dependencies are the only install requirements. The other 
# imports come with the Python 3 standard distribution. Use pip or conda to 
# install netCDF4 inside a virtual environment for best results. 
# 
# The `conda-forge` channel seems to provide a stable source for netCDF4:
# 
# ```shell
# conda install -c conda-forge netCDF4
# ```
#
"""
from sys import argv
from shutil import move
from subprocess import call
from os.path import basename
from datetime import datetime as dt, timedelta
from os.path import join, isfile, basename, dirname
from netCDF4 import Dataset, date2num, numpy as np

# Our preferred ISO datetime format:
dtfmt = "%Y-%m-%dT%H:%M:%S"

# Get a tstamp marking the time of file generation start:
tstamp = dt.utcnow().strftime(dtfmt)


class Configuration:
    """# Configuration
    
    This class provides a consistent way to configure the script. It can be 
    tweaked to support literally any netCDF file operation supported by the C
    library -- they're all exposed in some form to Python.
    
    The presets defined below instruct the script to write a revised copy of
    an input netCDF file that is formatted like the outputs for the CYGNSS 
    L3 Soil Moisture Product (Chew & Small, 2020) hosted at UCAR/COSMIC. The
    changes are implemented in a consistent and reliable way, with no changes
    to data itself.

    ## Configuring attributes
    
    Configure the global attributes in the class attribute named `attributes`,
    which stores a Python dictionary. NOTE: Those present to `None` should be 
    derived by `__init__`!

    ## Configuring variables
    
    For now, the only available attributes for us to configure correspond to 
    the netCDF variables. They store dictionaries of attributes to assign to 
    the variables in the output file.

    """
    vfill = -9999.
    vfilled = ['timeintervals', 'SIGMA_daily', 'SM_daily', 'SM_subdaily', 'SIGMA_subdaily']
    variables = {
        'SIGMA_daily': {
            'comment': "units represent soil moisture content as a fractional volume (cm3 cm-3)",
            'long_name': "standard deviation of soil moisture retrievals during the 24 hr period for the grid cell",
            'units': "1",
            #'coordinates': "longitude latitude",
            'coverage_content_type': "modelResult",
        },
        'SM_daily': {
            'comment': "units represent soil moisture content as a fractional volume (cm3 cm-3)",
            'long_name': "mean soil moisture retrieval during the daily time periods for the grid cell",
            'units': "1",
            #'coordinates': "longitude latitude",
            'coverage_content_type': "modelResult",
        },
        'SM_subdaily': {
            'comment': "units represent soil moisture content as a fractional volume (cm3 cm-3)",
            'long_name': "mean soil moisture retrieval during the sub-daily time periods for the grid cell",
            'units': "1",
            #'coordinates': "longitude latitude",
            'coverage_content_type': "modelResult",
        },
        'SIGMA_subdaily': {
            'comment': "units represent soil moisture content as a fractional volume (cm3 cm-3)",
            'long_name': "standard deviation of soil moisture retrievals during the sub-daily time periods for the grid cell",
            'units': "1",
            #'coordinates': "longitude latitude",
            'coverage_content_type': "modelResult",
        },
        'latitude': {
            'standard_name': "latitude",
            'long_name': "latitude",
            'axis': "Y",
            'units': "degrees_north",
            'coverage_content_type': "coordinate",
        },
        'longitude': {
            'standard_name': "longitude",
            'long_name': "longitude",
            'axis': "X",
            'units': "degrees_east",
            'coverage_content_type': "coordinate",
        },
        'time': {
            'standard_name': "time",
            'long_name': "time",
            #'axis': "T",
            'units': "days since 1970-01-01 00:00:00 UTC",
            'coverage_content_type': "referenceInformation",
        },
        'timeintervals': {
            'long_name': "start and stop time for the sub-daily time periods",
            'units': "hours",
            'coverage_content_type': "referenceInformation",
        },
    }

    attributes = {
        'source': None,
        'id': "PODAAC-CYGNU-L3SM1",
        'ShortName': "CYGNSS_L3_SOIL_MOISTURE_V1.0",
        'title': "CYGNSS Level 3 Soil Moisture from UCAR/CU",
        'summary': "The CYGNSS Level 3 Soil Moisture Product provides volumetric water content estimates for soils between 0-5 cm depth at a 6-hour discretization for most of the subtropics. The data were produced by CYGNSS investigators at the University Corporation for Atmospheric Research (UCAR) and the University Colorado at Boulder (CU), and derive from version 2.1 of the CYGNSS L1 SDR. The soil moisture algorithm uses collocated soil moisture retrievals from SMAP to calibrate CYGNSS observations from the same day. For a given location, a linear relationship between the SMAP soil moisture and CYGNSS reflectivity is determined and used to transform the CYGNSS observations into soil moisture. The data are archived in daily files in netCDF-4 format. Two soil moisture variables report the volumetric water content in units of cm3/cm3. The variable SM_subdaily includes up to four soil moisture estimates per day. Another variable SM_daily provides a daily average. The time series covers the period from March 2017 to August 2020.",
        'comment': "Dataset created by UCAR and CU Boulder",
        'program': "CYGNSS",
        'project': "CYGNSS",
        'institution': "COSMIC Data Analysis and Archive Center, Constellation Observing System for Meteorology, Ionosphere and Climate, University Corporation for Atmospheric Research (UCAR/COSMIC/CDAAC)",
        'references': "Chew, C.; Small, E. Description of the UCAR/CU Soil Moisture Product. Remote Sens. 2020, 12, 1558. https://doi.org/10.3390/rs12101558",
        'keywords_vocabulary': "NASA Global Change Master Directory (GCMD) Science Keywords",
        'keywords': "EARTH SCIENCE > LAND SURFACE > SOILS > SOIL MOISTURE/WATER CONTENT",
        'Conventions': "CF-1.6,ACDD-1.3",
        'license': "Freely Distributed",
        'version': None,
        'history': None,
        'cdm_data_type': "Grid",
        'creator_name': "Clara Chew, Eric Small",
        'creator_type': "person, person",
        'creator_url': "https://staff.ucar.edu/users/clarac, http://geode.colorado.edu/~small/",
        'creator_email': "claraac@ucar.edu, eric.small@colorado.edu",
        'creator_institution': "UCAR/COSMIC/CDAAC, UCO",
        'publisher_name': "PO.DAAC",
        'publisher_email': "podaac@podaac.jpl.nasa.gov",
        'publisher_type': "institution",
        'publisher_url': "https://podaac.jpl.nasa.gov",
        'publisher_institution': "NASA/JPL/PODAAC",
        'processing_level': "3",
        'geospatial_lat_min': None,
        'geospatial_lat_max': None,
        'geospatial_lat_units': "degrees_north",
        'geospatial_lon_min': None,
        'geospatial_lon_max': None,
        'geospatial_lon_units': "degrees_east",
        'time_coverage_start': None,
        'time_coverage_end': None,
        'time_coverage_duration': "P1D",
        'date_created': None,
        'date_modified': tstamp,
        'date_issued': tstamp,
    }

    def __init__(self, file: str):
        self.file = file

        # Outputs will be written to adjacent files and prefixed with "_".
        self.output = join(dirname(file), f"_{basename(file)}")

        # Get the file's creation timestamp as a Python datetime.        
        self.timed = dt.strptime(basename(file)[-11:-3], "%Y_%j")
        # Add twelve hours to the time to shift to middle of the day.
        self.timed = self.timed + timedelta(hours=12)
        # Determine an epoch time for the time variable based on the filename.
        self.timev = [date2num(self.timed, self.variables['time']['units'])]

        # Open the netCDF dataset in read mode.
        with Dataset(file, mode="r") as source:
            # Grab arrays for the latitude and longitude variables in source.
            lat = source.variables['latitude'][:]
            lon = source.variables['longitude'][:]
            # Grab some attributes from source dataset for manipulation.
            _hist = getattr(source, "History")
            _vers = getattr(source, "Version")
            
            # Creation date is stored in two formats in the source files:
            try:
                _created = dt.strptime(_hist[8:19], "%d-%b-%Y").strftime(dtfmt)
            except ValueError as e:
                _created = dt.strptime(_hist[8:18], "%Y-%m-%d").strftime(dtfmt)
            except Exception as e:
                # Handle only expected exception gracefully. Raise all others.
                raise e

        # Update any dynamic configuration based on the input file's content.
        self.attributes.update({
            'source': basename(file),
            'version': float(_vers.replace("version ","")),
            'history': f"{_hist}. Modified for PODAAC release {tstamp}.",
            'geospatial_lat_min': lat.min(),
            'geospatial_lat_max': lat.max(),
            'geospatial_lon_min': lon.min(),
            'geospatial_lon_max': lon.max(),
            'time_coverage_start': self.timed.strftime("%Y-%m-%dT00:00:00"),
            'time_coverage_end': self.timed.strftime("%Y-%m-%dT23:59:59"),
            'date_created': _created,
        })



def main(file: str, fill=-9999.):
    
    # Initialize the Configuration class object with the input file.
    conf = Configuration(file)

    # Open source netCDF in read mode, target netCDF in write mode.
    with Dataset(file, "r") as source, Dataset(conf.output, "w") as target:

        # Add a time dimension (length=unlimited/None):
        target.createDimension("time", size=1)
        # Add a time variable, which will be length=1 in this file:
        time = target.createVariable("time", "f4", ("time",))
        # Assign the time variable's attributes from the config.
        time.setncatts(conf.variables['time'])
        # Add one-item data array for time produced on `Configuration` init.
        time[:] = [conf.timev]

        # Loop over source dataset's dimensions, add them to the target dataset.
        for n, d in source.dimensions.items():
            target.createDimension(n, len(d) if not d.isunlimited() else None)

        # Loop over source dataset variables and create in target dataset.
        for n, v in source.variables.items():
            print(n)
            # Select the array of data for the variable. No fill by default.
            data, dims, fill = source.variables[n].__array__(), v.dimensions, None
            
            # If configured, set fill value for variable and replace its NaNs.
            if n in conf.vfilled:
                fill = conf.vfill
                data[data==np.nan] = fill

            # If var is lat or lon, rotate by 2d method; if data, by 3d method.
            if n in ['latitude', 'longitude']:
                data = np.rot90(data, k=1)
                dims = ('rows', 'columns')
            elif not n.startswith("time"):
                if n.endswith("_subdaily"):
                    data = np.rot90(data, k=1, axes=(1,2,))
                    dims = ('timeslices', 'rows', 'columns')
                elif n.endswith("_daily"):
                    data = np.rot90(data, k=1)
                    data = data[np.newaxis, ...]
                    dims = ('time', 'rows', 'columns')

            # Create the currently iterated variable in the target dataset.
            x = target.createVariable(n, v.datatype, dims, fill_value=fill)
            # Copy variable array from the source to the target dataset.
            target.variables[n][:] = data
            # Assign the configured attributes to the output variable.
            target[n].setncatts(Configuration.variables[n])

            target.sync()
            
        # Now is a convenient time to rename lat/lon dims in target dataset.
        target.renameDimension("rows", "lat")
        target.renameDimension("columns", "lon")
        
        # And set globals in target netCDF using a mega-jumbo-frankstein dict.
        target.setncatts(conf.attributes)
        
        # Sync staged data modifications to the target netCDF.
        target.sync()



if __name__ == "__main__":
    TEST = "level3/2017/077/ucar_cu_cygnss_sm_v1_2017_077.nc"
    try:
        f = argv[1]
    except IndexError as e:
        raise e
    except Exception as e:
        raise e
    else:
        if not isfile(f):
            raise Exception(f"ERROR: Path to source nc is not valid ({f})")
        elif basename(f)=="ucar_cu_cygnss_sm_v1_static_flags.nc":
            print("SKIPPING: level3/ucar_cu_cygnss_sm_v1_static_flags.nc")
        else:
            # Only if ALL conditions are satisfied, call main.
            main(file=f)