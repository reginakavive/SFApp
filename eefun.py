import ee
import streamlit as st
from google.cloud import storage

def authenticate_implicit_with_adc(project_id="google-earth-engine"):
    client = storage.Client("google-earth-engine")
    bucket = client.get_bucket("eia2030")

# # # Need to refresh token every week
ee.Authenticate()
ee.Initialize(project='midyear-button-379815')

# #############################################################################################################################
    # Define all required functions 

#function to save uploaded AOI
st.cache_data 
def save_uploaded_aoi(file_content, file_name):
    #Save the uploaded file to a temporary directory
    import tempfile
    import os
    import uuid
    _, file_extension = os.path.splitext(file_name)
    file_id = str(uuid.uuid4())
    file_path = os.path.join(tempfile.gettempdir(), f"{file_id}{file_extension}")
    with open(file_path, "wb") as file:
        file.write(file_content.getbuffer())
    return file_path

#function to get AOI bounding box
st.cache_data 
def bbox(coord_list):
     box = []
     for i in (0,1):
         res = sorted(coord_list, key=lambda x:x[i])
         box.append((res[0][i],res[-1][i]))
     ret = f"({box[0][0]} {box[1][0]}, {box[0][1]} {box[1][1]})"
     return ret


    
def means(col, band, sdate, edate, bb):
    img = ee.ImageCollection(col).filterDate(sdate, edate).filterBounds(bb).select(band).map(clipbb).mean().rename(band)
    return img



#Compute moving-window variance.
def moving_var (i):
    img = ee.Image(i.reduceNeighborhood(reducer= ee.Reducer.variance(),kernel=ee.Kernel.square(7)))
    return img

zS = ee.Reducer.median().combine(**{
  'reducer2': ee.Reducer.mode(),
  'sharedInputs': True
})


def zMed(img, collection):
    stats = img.reduceRegions(**{
        'collection': collection,
        'reducer': zS,
        'scale': 500,
        'crs': 'EPSG:4326'
    })
    return stats

# Zonale statistics by image - mod
def zMod (img, collection):
    stats = img.reduceRegions(
    collection=collection,
    reducer=ee.Reducer.mod(),
    scale=500,
    crs='EPSG:4326'
  ),
    return stats 

def clustererK (k):
    return ee.Clusterer.wekaKMeans(nClusters = k, seed = ee.Number(99))


def NrdF (image):
    rd = image.gte(1)
    return rd

def subset(feature, selected_variables):
    # Mapping selected variables to their respective properties
    properties_mapping = {
        'Rainfall Total': '0_prcSum_median',
        'Rainfall Days': '1_prcNrd_median',
        'Rainfall Average': '2_Di_median',
        'Temperature Maximum': '3_tmaxMax_median',
        'Temperature Minimum': '4_tminMin_median',
        'Temperature Mean': '5_tmeanMean_median',
        'Soil Zinc': '6_zinc_median',
        'Elevation': '7_srtm_median'
    }
    
    # Filtering out properties not in the selected variables list
    selected_properties = [properties_mapping[var] for var in selected_variables if var in properties_mapping]
    

    # Creating a feature with only selected properties
    selected_properties_dict = {var: feature.get(properties_mapping[var]) for var in selected_variables if var in properties_mapping}
    f = ee.Feature(feature.geometry(), selected_properties_dict).copyProperties(feature, selected_properties)
    
    return f




def subs (feature):
    keepProperties = ['label']
    f = ee.Feature(feature.geometry(), {'cluster': feature.get('label')}).copyProperties(feature, keepProperties)
    return f
    
def zz(img, collection):
    stats = img.reduceRegions(**{
        'collection': collection,
        'reducer': ee.Reducer.mean(),
        'scale': 500,
        'crs': 'EPSG:4326'
    })
    return stats




cropmask = ee.Image('COPERNICUS/Landcover/100m/Proba-V-C3/Global/2019').select('discrete_classification').eq(40)


# //////////////////////////////////////////////////////////////////////////////////////////////
    # // 2 - Get Co-Variables
    # //////////////////////////////////////////////////////////////////////////////////////////////
    # // Primary Variables and preprocess
st.cache_data 
def prcSum(selected_Sdate, selected_Edate,sdate, edate,bb):
    # // Rainfall
    prc = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY') \
                      .filter(ee.Filter.date(sdate, edate)) \
                      .filter(ee.Filter.calendarRange(int(selected_Sdate.strftime("%-m")), int((selected_Edate).strftime("%-m")),'month')) \
                      .select('precipitation')
    
    prcSum = prc.reduce(ee.Reducer.sum()).clip(bb)
    return prcSum

st.cache_data 
def prcNrd(selected_Sdate, selected_Edate,sdate, edate,bb):    
    prc = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY') \
                      .filter(ee.Filter.date(sdate, edate)) \
                      .filter(ee.Filter.calendarRange(int(selected_Sdate.strftime("%-m")), int((selected_Edate).strftime("%-m")),'month')) \
                      .select('precipitation')
    Nrd = prc.map(NrdF)    
    prcNrd = Nrd.reduce(ee.Reducer.sum()).clip(bb)
    return prcNrd

st.cache_data 
def Di(selected_Sdate, selected_Edate,sdate, edate,bb):
    prc = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY') \
                      .filter(ee.Filter.date(sdate, edate)) \
                      .filter(ee.Filter.calendarRange(int(selected_Sdate.strftime("%-m")), int((selected_Edate).strftime("%-m")),'month')) \
                      .select('precipitation')
    
    prcSum = prc.reduce(ee.Reducer.sum()).clip(bb)    
    Nrd = prc.map(NrdF)    
    prcNrd = Nrd.reduce(ee.Reducer.sum()).clip(bb)    
    Di = prcSum.divide(prcNrd)
    return Di
    
    
    # // Temperature
st.cache_data 
def tminMin(selected_Sdate, selected_Edate,sdate, edate,bb):
    tmin = ee.ImageCollection('ECMWF/ERA5/DAILY') \
                      .select('minimum_2m_air_temperature') \
                      .filter(ee.Filter.date(sdate, edate)) \
                      .filter(ee.Filter.calendarRange(int(selected_Sdate.strftime("%-m")), int((selected_Edate).strftime("%-m")),'month')) 
    
    tminMin = tmin.reduce(ee.Reducer.min()).clip(bb)
    return tminMin
    
st.cache_data 
def tmaxMax(selected_Sdate, selected_Edate,sdate, edate,bb):
    tmax = ee.ImageCollection('ECMWF/ERA5/DAILY') \
                      .select('maximum_2m_air_temperature') \
                      .filter(ee.Filter.date(sdate, edate)) \
                      .filter(ee.Filter.calendarRange(int(selected_Sdate.strftime("%-m")), int((selected_Edate).strftime("%-m")),'month')) 
    
    tmaxMax = tmax.reduce(ee.Reducer.max()).clip(bb)
    return tmaxMax

st.cache_data 
def tmeanMean(selected_Sdate, selected_Edate,sdate, edate,bb):
    tmean = ee.ImageCollection('ECMWF/ERA5/DAILY') \
                      .select('mean_2m_air_temperature') \
                      .filter(ee.Filter.date(sdate, edate)) \
                      .filter(ee.Filter.calendarRange(int(selected_Sdate.strftime("%-m")), int((selected_Edate).strftime("%-m")),'month')) 
    
    tmeanMean = tmean.reduce(ee.Reducer.mean()).clip(bb);
    return tmeanMean

    #     # // Soil
st.cache_data 
def zinc(bb):    
    zinc = ee.Image("ISDASOIL/Africa/v1/zinc_extractable").select('mean_0_20', 'mean_20_50')
    zinc = zinc.reduce(ee.Reducer.mean()).clip(bb)
    return zinc
    
    # // Elevation
st.cache_data 
def srtm(bb):
    srtm = ee.Image('CGIAR/SRTM90_V4').select('elevation').clip(bb)
    return srtm 
    #slp = ee.Terrain.slope(srtm)

st.cache_data 
def slp(bb):
    srtm = ee.Image('CGIAR/SRTM90_V4').select('elevation').clip(bb)
    slp = ee.Terrain.slope(srtm)
    return slp



    #     # // Soil
    # SOC = ee.Image("projects/soilgrids-isric/ocd_mean") \
    #   .select('ocd_0-5cm_mean', 'ocd_5-15cm_mean','ocd_15-30cm_mean')
    # SOCmean = SOC.reduce(ee.Reducer.mean()).clip(bb)
    
    # pH = ee.Image("projects/soilgrids-isric/phh2o_mean") \
    #  .select('phh2o_0-5cm_mean', 'phh2o_5-15cm_mean','phh2o_15-30cm_mean')
    # pHmean = pH.reduce(ee.Reducer.mean()).clip(bb)
    
    # CEC = ee.Image("projects/soilgrids-isric/cec_mean").select('cec_0-5cm_mean', 'cec_5-15cm_mean','cec_15-30cm_mean')
    # CECmean = CEC.reduce(ee.Reducer.mean()).clip(bb)
    
    # N = ee.Image("projects/soilgrids-isric/nitrogen_mean").select('nitrogen_0-5cm_mean', 'nitrogen_5-15cm_mean','nitrogen_15-30cm_mean');
    # Nmean = N.reduce(ee.Reducer.mean()).clip(bb)
    
    # clay = ee.Image("projects/soilgrids-isric/clay_mean").select('clay_0-5cm_mean', 'clay_5-15cm_mean','clay_15-30cm_mean')
    # claymean = clay.reduce(ee.Reducer.mean()).clip(bb)
    
    # sand = ee.Image("projects/soilgrids-isric/sand_mean").select('sand_0-5cm_mean', 'sand_5-15cm_mean','sand_15-30cm_mean')
    # sandmean = sand.reduce(ee.Reducer.mean()).clip(bb)


st.cache_data 
def vectors(bb,selected_Sdate,selected_Edate,sdate,edate):
    # Rescale values between 0-1
    def rescale (img):
        mm = img.reduceRegion(reducer= ee.Reducer.minMax(), bestEffort=True, geometry= bb)
        mM = mm.rename(mm.keys(), ['max', 'min'])
        return mM 
    
    def clipbb(image):
        return image.clip(bb)
    
    def calcNDVI (image):
        scaled = image.unitScale(ee.Number(rescale(image).values().get(1)), rescale(image).values().get(0)).toFloat().rename('NDVI').clip(bb)
        return scaled
    
    def sStackF (image):
        i = image.mask(cropmask).clip(bb)
        return i
     # # #############################################################################################################################
    ## 1 - Landscape Segmentation
    dataset = ee.ImageCollection('MODIS/061/MOD13A2') \
                      .filter(ee.Filter.date(sdate, edate)) \
                      .filter(ee.Filter.calendarRange(int(selected_Sdate.strftime("%-m")), int((selected_Edate).strftime("%-m")),'month')) \
                      .select('NDVI')
    
    #Spatio-temporal rescaling of NDVI    
    ndvi = dataset.map(calcNDVI)
    
    # # Stack NDVI
    ndvi = ndvi.toBands()
    
    # Apply the SNIC algorithm to the image.
    snic = ee.Algorithms.Image.Segmentation.SNIC(
      image=ndvi,
      size=10,
      compactness=0.1,
      connectivity=8,
    )
    
    # Select the cluster band
    clusters_snic = snic.select("clusters")
    
    # // Vectorization of the cluster band
    
    vectors = clusters_snic.reduceToVectors(
       geometryType= 'polygon',
       scale= 250,
      geometry= bb,
    )
    return vectors

st.cache_data 
def stackk(bb,selected_Sdate,selected_Edate,sdate,edate,selected_variables,prcSum,  prcNrd, Di, tmaxMax ,tminMin ,tmeanMean,zinc,srtm):
    # Rescale values between 0-1
    def rescale (img):
        mm = img.reduceRegion(reducer= ee.Reducer.minMax(), bestEffort=True, geometry= bb)
        mM = mm.rename(mm.keys(), ['max', 'min'])
        return mM 
    
    def clipbb(image):
        return image.clip(bb)
    
    def calcNDVI (image):
        scaled = image.unitScale(ee.Number(rescale(image).values().get(1)), rescale(image).values().get(0)).toFloat().rename('NDVI').clip(bb)
        return scaled
    
    def sStackF (image):
        i = image.mask(cropmask).clip(bb)
        return i
    # //////////////////////////////////////////////////////////////////////////////////////////////
    # // 3 - Database shaping
    # //////////////////////////////////////////////////////////////////////////////////////////////
    properties_mapping = {
        'Rainfall Total': '0_prcSum',
        'Rainfall Days': '1_prcNrd',
        'Rainfall Average': '2_Di',
        'Temperature Maximum': '3_tmaxMax',
        'Temperature Minimum': '4_tminMin',
        'Temperature Mean': '5_tmeanMean',
        'Soil Zinc': '6_zinc',
        'Elevation': '7_srtm'
        }

    stack_variables = [properties_mapping[var] for var in selected_variables if var in properties_mapping]

    

    # // Stack
    stack = ee.ImageCollection.fromImages([
        prcSum.unitScale(ee.Number(rescale(moving_var(prcSum).reproject(crs= 'EPSG:4326', scale= 1000)).values().get(1)), rescale(prcSum.reproject(crs= 'EPSG:4326', scale= 1000)).values().get(0)).reproject(crs= 'EPSG:4326', scale= 1000).toFloat().rename('prcSum'),
        prcNrd.unitScale(ee.Number(rescale(moving_var(prcNrd).reproject(crs= 'EPSG:4326', scale=1000)).values().get(1)), rescale(prcNrd.reproject(crs='EPSG:4326', scale= 1000)).values().get(0)).reproject(crs= 'EPSG:4326', scale= 1000).toFloat().rename('prcNrd'),
        Di.unitScale(ee.Number(rescale(moving_var(Di).reproject(crs= 'EPSG:4326', scale= 1000)).values().get(1)), rescale(Di.reproject(crs= 'EPSG:4326', scale= 1000)).values().get(0)).reproject(crs= 'EPSG:4326', scale= 1000).toFloat().rename('Di'),
        tmaxMax.unitScale(ee.Number(rescale(moving_var(tmaxMax).reproject(crs= 'EPSG:4326', scale= 1000)).values().get(1)), rescale(tmaxMax.reproject(crs= 'EPSG:4326', scale= 1000)).values().get(0)).reproject(crs= 'EPSG:4326', scale= 1000).toFloat().rename('tmaxMax'),
        tminMin.unitScale(ee.Number(rescale(moving_var(tminMin).reproject(crs='EPSG:4326', scale= 1000)).values().get(1)), rescale(tminMin.reproject(crs='EPSG:4326', scale= 1000)).values().get(0)).reproject(crs= 'EPSG:4326', scale= 1000).toFloat().rename('tminMin'),
        tmeanMean.unitScale(ee.Number(rescale(moving_var(tmeanMean).reproject(crs= 'EPSG:4326', scale= 1000)).values().get(1)), rescale(tmeanMean.reproject(crs= 'EPSG:4326', scale= 1000)).values().get(0)).reproject(crs= 'EPSG:4326', scale= 1000).toFloat().rename('tmeanMean'),
        zinc.unitScale(ee.Number(rescale(zinc.reproject(crs= 'EPSG:4326', scale= 1000)).values().get(1)), rescale(zinc.reproject(crs='EPSG:4326', scale= 1000)).values().get(0)).reproject(crs= 'EPSG:4326', scale= 1000).toFloat().rename('zinc'),
        srtm.unitScale(ee.Number(rescale(srtm.reproject(crs= 'EPSG:4326', scale= 1000)).values().get(1)), rescale(srtm.reproject(crs= 'EPSG:4326', scale= 1000)).values().get(0)).reproject(crs= 'EPSG:4326', scale= 1000).toFloat().rename('srtm')
    ])

    
    stack = stack.toBands()
    stack = stack.select(stack_variables)
    return stack

st.cache_data 
def get_training(bb,vectors,selected_variables,prcSum,  prcNrd, Di, tmaxMax ,tminMin ,tmeanMean,zinc,srtm):
    # Rescale values between 0-1
    def rescale (img):
        mm = img.reduceRegion(reducer= ee.Reducer.minMax(), bestEffort=True, geometry= bb)
        mM = mm.rename(mm.keys(), ['max', 'min'])
        return mM 
    
    def clipbb(image):
        return image.clip(bb)
    
    def calcNDVI (image):
        scaled = image.unitScale(ee.Number(rescale(image).values().get(1)), rescale(image).values().get(0)).toFloat().rename('NDVI').clip(bb)
        return scaled
    
    def sStackF (image):
        i = image.mask(cropmask).clip(bb)
        return i

     # //////////////////////////////////////////////////////////////////////////////////////////////
    # // 3 - Database shaping
    # //////////////////////////////////////////////////////////////////////////////////////////////
    properties_mapping = {
        'Rainfall Total': '0_prcSum',
        'Rainfall Days': '1_prcNrd',
        'Rainfall Average': '2_Di',
        'Temperature Maximum': '3_tmaxMax',
        'Temperature Minimum': '4_tminMin',
        'Temperature Mean': '5_tmeanMean',
        'Soil Zinc': '6_zinc',
        'Elevation': '7_srtm'
        }

    stack_variables = [properties_mapping[var] for var in selected_variables if var in properties_mapping]

    

    # // Stack
    stack = ee.ImageCollection.fromImages([
        prcSum.unitScale(ee.Number(rescale(moving_var(prcSum).reproject(crs= 'EPSG:4326', scale= 1000)).values().get(1)), rescale(prcSum.reproject(crs= 'EPSG:4326', scale= 1000)).values().get(0)).reproject(crs= 'EPSG:4326', scale= 1000).toFloat().rename('prcSum'),
        prcNrd.unitScale(ee.Number(rescale(moving_var(prcNrd).reproject(crs= 'EPSG:4326', scale=1000)).values().get(1)), rescale(prcNrd.reproject(crs='EPSG:4326', scale= 1000)).values().get(0)).reproject(crs= 'EPSG:4326', scale= 1000).toFloat().rename('prcNrd'),
        Di.unitScale(ee.Number(rescale(moving_var(Di).reproject(crs= 'EPSG:4326', scale= 1000)).values().get(1)), rescale(Di.reproject(crs= 'EPSG:4326', scale= 1000)).values().get(0)).reproject(crs= 'EPSG:4326', scale= 1000).toFloat().rename('Di'),
        tmaxMax.unitScale(ee.Number(rescale(moving_var(tmaxMax).reproject(crs= 'EPSG:4326', scale= 1000)).values().get(1)), rescale(tmaxMax.reproject(crs= 'EPSG:4326', scale= 1000)).values().get(0)).reproject(crs= 'EPSG:4326', scale= 1000).toFloat().rename('tmaxMax'),
        tminMin.unitScale(ee.Number(rescale(moving_var(tminMin).reproject(crs='EPSG:4326', scale= 1000)).values().get(1)), rescale(tminMin.reproject(crs='EPSG:4326', scale= 1000)).values().get(0)).reproject(crs= 'EPSG:4326', scale= 1000).toFloat().rename('tminMin'),
        tmeanMean.unitScale(ee.Number(rescale(moving_var(tmeanMean).reproject(crs= 'EPSG:4326', scale= 1000)).values().get(1)), rescale(tmeanMean.reproject(crs= 'EPSG:4326', scale= 1000)).values().get(0)).reproject(crs= 'EPSG:4326', scale= 1000).toFloat().rename('tmeanMean'),
        zinc.unitScale(ee.Number(rescale(zinc.reproject(crs= 'EPSG:4326', scale= 1000)).values().get(1)), rescale(zinc.reproject(crs='EPSG:4326', scale= 1000)).values().get(0)).reproject(crs= 'EPSG:4326', scale= 1000).toFloat().rename('zinc'),
        srtm.unitScale(ee.Number(rescale(srtm.reproject(crs= 'EPSG:4326', scale= 1000)).values().get(1)), rescale(srtm.reproject(crs= 'EPSG:4326', scale= 1000)).values().get(0)).reproject(crs= 'EPSG:4326', scale= 1000).toFloat().rename('srtm')
    ])

    
    #stack = stack.toBands()
    
    # Mapping selected variables to their respective properties
    properties_mapping = {
        'Rainfall Total': '0_prcSum_median',
        'Rainfall Days': '1_prcNrd_median',
        'Rainfall Average': '2_Di_median',
        'Temperature Maximum': '3_tmaxMax_median',
        'Temperature Minimum': '4_tminMin_median',
        'Temperature Mean': '5_tmeanMean_median',
        'Soil Zinc': '6_zinc_median',
        'Elevation': '7_srtm_median'
    }

    # Filtering out properties not in the selected variables list
    selected_properties = [properties_mapping[var] for var in selected_variables if var in properties_mapping]
    
  
    sStack = stack.map(sStackF)    
    
    # // Zonal statistics
    sSStack = sStack.toBands()
    
    zsStack = zMed(sSStack, vectors)
    zsStack = ee.FeatureCollection(zsStack)
    
    
    # zz = ee.FeatureCollection(zsStack)

    #training = zsStack.map(subset)
    training = zsStack.map(lambda feature: subset(feature, selected_variables)) 
    return training
    
st.cache_data 
def get_x(training,selected_variables):
    # Rescale values between 0-1
    def rescale (img):
        mm = img.reduceRegion(reducer= ee.Reducer.minMax(), bestEffort=True, geometry= bb)
        mM = mm.rename(mm.keys(), ['max', 'min'])
        return mM 
    
    def clipbb(image):
        return image.clip(bb)
    
    def calcNDVI (image):
        scaled = image.unitScale(ee.Number(rescale(image).values().get(1)), rescale(image).values().get(0)).toFloat().rename('NDVI').clip(bb)
        return scaled
    
    def sStackF (image):
        i = image.mask(cropmask).clip(bb)
        return i
        
    # Mapping selected variables to their respective properties
    properties_mapping = {
        'Rainfall Total': '0_prcSum_median',
        'Rainfall Days': '1_prcNrd_median',
        'Rainfall Average': '2_Di_median',
        'Temperature Maximum': '3_tmaxMax_median',
        'Temperature Minimum': '4_tminMin_median',
        'Temperature Mean': '5_tmeanMean_median',
        'Soil Zinc': '6_zinc_median',
        'Elevation': '7_srtm_median'
    }

    # Filtering out properties not in the selected variables list
    selected_properties = [properties_mapping[var] for var in selected_variables if var in properties_mapping]
    
    # Filter out features with null values for selected properties
    trainingNoNulls = training.filter(ee.Filter.notNull(selected_properties))
    
    # Construct the ee.ImageCollection
    image_collection = []
    for prop in selected_properties:
        image = trainingNoNulls.reduceToImage(properties=[prop], reducer=ee.Reducer.first()).rename(prop)
        image_collection.append(image)
    
    # Convert the list of images to an ee.ImageCollection
    x = ee.ImageCollection.fromImages(image_collection).toBands()    
    # Rename the bands
    band_names = ['{}_{}'.format(i, prop) for i, prop in enumerate(selected_properties)]
    x = x.rename(band_names)    
    # Rename the bands to original median names
    x = x.rename(selected_properties)
    return (x)

st.cache_data 
def get_res_xmeans(training,selected_variables,x):
    # Rescale values between 0-1
    def rescale (img):
        mm = img.reduceRegion(reducer= ee.Reducer.minMax(), bestEffort=True, geometry= bb)
        mM = mm.rename(mm.keys(), ['max', 'min'])
        return mM 
    
    def clipbb(image):
        return image.clip(bb)
    
    def calcNDVI (image):
        scaled = image.unitScale(ee.Number(rescale(image).values().get(1)), rescale(image).values().get(0)).toFloat().rename('NDVI').clip(bb)
        return scaled
    
    def sStackF (image):
        i = image.mask(cropmask).clip(bb)
        return i
        
    # Mapping selected variables to their respective properties
    properties_mapping = {
        'Rainfall Total': '0_prcSum_median',
        'Rainfall Days': '1_prcNrd_median',
        'Rainfall Average': '2_Di_median',
        'Temperature Maximum': '3_tmaxMax_median',
        'Temperature Minimum': '4_tminMin_median',
        'Temperature Mean': '5_tmeanMean_median',
        'Soil Zinc': '6_zinc_median',
        'Elevation': '7_srtm_median'
    }

    # Filtering out properties not in the selected variables list
    selected_properties = [properties_mapping[var] for var in selected_variables if var in properties_mapping]
    
    # Filter out features with null values for selected properties
    trainingNoNulls = training.filter(ee.Filter.notNull(selected_properties))
    
    #// Instantiate the clusterer and train it.
    clusterer = ee.Clusterer.wekaXMeans(
        minClusters= 1,
        maxClusters=100,
        maxIterations=500,
        seed= 99).train(
        features=trainingNoNulls,
        inputProperties= selected_properties
    )

    #// Cluster the input using the trained clusterer.
    res = x.cluster(clusterer)
    
    return (res)

st.cache_data 
def get_res_kmeans(training,selected_variables,cluster_selection,x):
    # Rescale values between 0-1
    def rescale (img):
        mm = img.reduceRegion(reducer= ee.Reducer.minMax(), bestEffort=True, geometry= bb)
        mM = mm.rename(mm.keys(), ['max', 'min'])
        return mM 
    
    def clipbb(image):
        return image.clip(bb)
    
    def calcNDVI (image):
        scaled = image.unitScale(ee.Number(rescale(image).values().get(1)), rescale(image).values().get(0)).toFloat().rename('NDVI').clip(bb)
        return scaled
    
    def sStackF (image):
        i = image.mask(cropmask).clip(bb)
        return i

    
    # Mapping selected variables to their respective properties
    properties_mapping = {
        'Rainfall Total': '0_prcSum_median',
        'Rainfall Days': '1_prcNrd_median',
        'Rainfall Average': '2_Di_median',
        'Temperature Maximum': '3_tmaxMax_median',
        'Temperature Minimum': '4_tminMin_median',
        'Temperature Mean': '5_tmeanMean_median',
        'Soil Zinc': '6_zinc_median',
        'Elevation': '7_srtm_median'
    }

    # Filtering out properties not in the selected variables list
    selected_properties = [properties_mapping[var] for var in selected_variables if var in properties_mapping]
    
    # Filter out features with null values for selected properties
    trainingNoNulls = training.filter(ee.Filter.notNull(selected_properties))
    
    k = ee.Number(cluster_selection)

    clustererKW = clustererK(k).train(features = trainingNoNulls, inputProperties = selected_properties)
            
    res = x.cluster(clustererKW)
    return (res)

st.cache_data 
def download_data(res,stack,bb,selected_variables,prcSum,  prcNrd, Di, tmaxMax ,tminMin ,tmeanMean,zinc,srtm):    
    out = str(".")
    # Rescale values between 0-1
    def rescale (img):
        mm = img.reduceRegion(reducer= ee.Reducer.minMax(), bestEffort=True, geometry= bb)
        mM = mm.rename(mm.keys(), ['max', 'min'])
        return mM 
    
    def clipbb(image):
        return image.clip(bb)
    
    def calcNDVI (image):
        scaled = image.unitScale(ee.Number(rescale(image).values().get(1)), rescale(image).values().get(0)).toFloat().rename('NDVI').clip(bb)
        return scaled
    
    def sStackF (image):
        i = image.mask(cropmask).clip(bb)
        return i

    

    cks = res.reduceToVectors(
      geometryType= 'polygon',
      scale= 250, #// THIS IS KEY!!!!
      geometry= bb
    )
    
    fcks = zMed(stack, cks)
    
    fcksStyles = ee.Dictionary({
        0: {'color': '0e6626','fillColor': '0e662688'},
        1: {'color': 'de6c52','fillColor': 'de6c5288'},
        2: {'color': '645ff5','fillColor': '645ff588'},
        3: {'color': 'a63393','fillColor': 'a6339388'},
        4: {'color': 'f5f10c','fillColor': 'f5f10c88'},
        5: {'color': '4ecf2d','fillColor': '4ecf2d88'},
        6: {'color': '89d699','fillColor': '89d69988'},
        7: {'color': 'edbc34','fillColor': 'edbc3488'},
        8: {'color': 'd4857f','fillColor': 'd4857f88'},
        9: {'color': '6dbd7b','fillColor': '6dbd7b88'},
        10: {'color': '112fc2','fillColor': '112fc288'},
        11: {'color': 'ab6e68','fillColor': 'ab6e6888'},
        12: {'color': 'a1f73e','fillColor': 'a1f73e88'},
        13: {'color': '73f5f0','fillColor': '73f5f088'},
        14: {'color': '933cc9','fillColor': '933cc988'},
        15: {'color': 'd263e0','fillColor': 'd263e088'},
        16: {'color': '42468c','fillColor': '42468c88'},
        17: {'color': 'bf2608','fillColor': 'bf260888'},
        18: {'color': '56a391','fillColor': '56a39188'},
        19: {'color': 'a9a7e8','fillColor': 'a9a7e888'}
        })
    #// Add feature-specific style properties to each feature based on fuel type.
    def fcksfn (feature): 
        return feature.set('style', fcksStyles.get(feature.get('label')))
                    
    fcks = ee.FeatureCollection(fcks).map(fcksfn)
    
    #// Style the FeatureCollection according to each feature's "style" property.
    fcksVisCustom = fcks.style(
      styleProperty='style' 
    )

       
    data = ee.ImageCollection.fromImages([
    
      prcSum.reproject(crs= 'EPSG:4326', scale= 1000).rename('RainfallTotal'),
    
      prcNrd.reproject(crs= 'EPSG:4326', scale= 1000).rename('RainfallDays'),
    
      Di.reproject(crs= 'EPSG:4326', scale= 1000).rename('RainfallAverage'),
    
      tmaxMax.reproject(crs= 'EPSG:4326', scale= 1000).rename('TemperatureMax'),
    
      tminMin.reproject(crs= 'EPSG:4326', scale= 1000).rename('TemperatureMin'),
    
      tmeanMean.reproject(crs= 'EPSG:4326', scale= 1000).rename('TemperatureMean'),
    
     # // SOCmean.reproject(crs= 'EPSG:4326', scale= 1000).rename('SoilCarbon'),
    
      #// pHmean.reproject(crs= 'EPSG:4326', scale=1000).rename('SoilpH'),
    
      #// CECmean.reproject(crs= 'EPSG:4326', scale= 1000).rename('SoilCEC'),
    
      #// Nmean.reproject(crs= 'EPSG:4326', scale= 1000).rename('SoilNitrogen'),
    
      zinc.reproject(crs= 'EPSG:4326', scale= 1000).rename('SoilZinc'),
    
      #// claymean.reproject(crs= 'EPSG:4326', scale= 1000).rename('SoilClay'),
    
      #// sandmean.reproject(crs= 'EPSG:4326', scale= 1000).rename('SoilSand'),
    
      srtm.reproject(crs= 'EPSG:4326', scale= 1000).rename('Elevation')
    
      #// slp.reproject(crs= 'EPSG:4326', scale= 1000).rename('Slope'),
    
      # // relh.reproject(crs= 'EPSG:4326', scale= 1000).rename('RelativeHumidity')
    ])
    
    # Mapping selected variables to their respective properties
    properties_mapping = {
            'Rainfall Total': '0_RainfallTotal',
            'Rainfall Days': '1_RainfallDays',
            'Rainfall Average': '2_RainfallAverage',
            'Temperature Maximum': '3_TemperatureMax',
            'Temperature Minimum': '4_TemperatureMin',
            'Temperature Mean': '5_TemperatureMean',
            'Soil Zinc': "6_SoilZinc",
            'Elevation': '7_Elevation'
            }
    
    
    # Filtering out properties not in the selected variables list
    selected_properties = [properties_mapping[var] for var in selected_variables if var in properties_mapping]
    
    data = data.toBands()
    data = data.select(selected_properties)
    
    out = ee.FeatureCollection(fcks).map(subs)
    
    out = zz(data, out)
    
    #// Dissolve by cluster and average attributes
    outProps = ee.List(out.aggregate_array('label')).distinct()
    totAreaHa =ee.Number.expression('x/y', {'x':out.geometry().area(maxError=1),'y':10000})           

    def propfn(prop, selected_properties):
        tempFC = out.filter(ee.Filter.eq('label', prop))
        unionFC = tempFC.union(1)
        clu = tempFC.aggregate_mean('label')
        
        # Dynamically aggregate only the selected properties
        aggregated_properties = {}
        for prop_name in selected_properties:
            prop_value = tempFC.aggregate_mean(prop_name)
            aggregated_properties[prop_name] = prop_value
        
        # Create feature with selected aggregated properties
        f = ee.Feature(tempFC.geometry(), {
            'cluster': ee.Number(prop),
            'trials': ee.Number.expression('(x/y)*100', {
                'x': ee.Number.expression('x/y', {'x': tempFC.geometry().area(maxError= 1), 'y': 10000}),
                'y': totAreaHa
            }).round(),
            **{prop_name: ee.Number(prop_value).format('%.3e') for prop_name, prop_value in aggregated_properties.items()}
        })
        return f
    
    
    outDiss = ee.FeatureCollection(outProps.map(lambda prop: propfn(prop, selected_properties)))
    return(outDiss)


