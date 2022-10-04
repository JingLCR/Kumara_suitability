# Kumara suitability
he land suitability concept is used to characterise the degree of fitness of a given environment for specific agricultural activities. To quantify land suitability for a given environment, the “biophysical attributes” are translated into “suitability indexes/classes” through crop-specific “suitability rules”. For example, suitable growing conditions might occur between temperature ranges of 11 to 38°C for kumara, with an optimum within a narrower range (e.g. 13 and 28°C). Suitability classes (four classes were defined - unsuitable, marginally suited, suitable, and well suited) for different attribute-crop combinations can be estimated based on such suitability rules. The suitability rules are simplifications of biophysically sound principles that operate at a much lower scale of organisation (e.g. crop and plant physiological responses to the environment). Such simplification is necessary, given that suitability assessments are performed at the landscape level.

The analytical method and dataflow were developed to process geo-referenced input data into suitability maps. Specifically, the suitability modelling framework utilises a wider range of GIS-rules adapting the method from Kidd et al. (2015) and simplified “categorical” parameter ranges. For method transparency and reproducibility, suitability parameters are stored in a single database. In the database, the biophysical-attributes for a given crop and their relationship to the four possible suitability classes are specified, this information is then called by the suitability model devaloped with Python.

The ruleset for Kumara suitability modelling is listed below. 
![image](https://user-images.githubusercontent.com/40552847/193713813-d4451f14-e08b-4df2-b2e7-6b3e00f22dcf.png)


References:

Kidd D, Webb M, Malone B, Minasny B, McBratney A. 2015. Digital soil assessment of agricultural suitability, versatility and capital in Tasmania, Australia. Geoderma Regional. 6: 7-21.


# Modelling steps

1. Data
Data reqired for Kumara suitability mapping including Soil - SMap (vector (file gdb)), Topography - Slope (raster (tif)) and Climate - Daily Temperature and Rainfall (raster (tif)).
Soil PH is another requried ratster layer as it has not been integrated into SMap yet. 
The 'pfr1ls_whole_smap_sharns_newrule_20220928.db' which has the latest ruleset for generating covariate layers and suitability mapping.

2. Preprocessing
1) Run 'add_new_fields.py' to add new attributes to SMap.
This step is to convert some non-numeric attributes to numeric attributes, including 'SiblingDrainageCode',  'NZSC' and 'SDP_MEAN'. The SMap format must be FileGDB which is allowed to have multiple siblings featureclasses.
The location of the SMap file can be specified in the 'config.ini' file.

2) Run 'soil_process.py' to rasterize soil data. 
This step will create 'GPKG' file and multiple GeoTiff files. For each sibiling featureclass, the unsuccessfully (due to the raster resolution) polygons is stored in a 
new featureclass for the next round rasterization. This procedue will repeat until all the polygons are rasterized. The number of raster files are corresponding to the number of featureclasses.
The resolution of ratster files can be specified in the 'config.ini' file.

3) Run 'terrain_process.py' to process slope and PH data.
This step including two parts. One is copy and rename the data and then resample/reproject the data to make them consistent with soil raster. The first part only need to be done once. 
But the second part will need to be repeated whenever the soil date is updated. When running the script, it will ask whether you'd like to only do the resampling. If you choose 'Yes', then it will only do the second part.

4) Run 'climate_process.py' to create climate covariate layers.
The step create kumara specific climate covariate layers from daily temperature and rainfall data. Similar to terrain process, the first part of generating the covariates can be only done once, but the resampling step need to be done whenever the soil data is updated.
The script gives prompt as well. Be aware this step might take long time to run depending on how many years of date used and raster resolution. There might be a chance encountering RAM overflow if the resolution is set to high (e.g. >50m).

3. Suitability mapping
Run 'land_suitability_mapping_v3.py' to map the kumara suitability. Again, each soil featureclass will have one corresponing suitability layer created.



    
