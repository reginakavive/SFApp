import ee
import folium
import geojson
import streamlit as st
import geopandas as gpd
import json
import geemap.foliumap as geemap
from google.cloud import storage
import datetime
import urllib.request
from shapely.geometry import mapping
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from PIL import Image
import math
import io
import re
import random
import pandas as pd
from eefun import *

logo = "assets/EiA_logo.png"
logo2 = "assets/EiA_logo2.png"

# Wide app layout
st.set_page_config(layout="wide", page_title="Sampling Framework", page_icon=logo2)
st.header(":green[Sampling Framework]")

crops = ["Rice","Potato","Maize", "Cassava", "Wheat", "Soybean", "Teff", "Sorghum" ]
varlist = ['Rainfall Total', 'Rainfall Days','Rainfall Average','Temperature Maximum',
            'Temperature Minimum','Temperature Mean','Soil Zinc', 'Elevation','Slope', 'Soil Organic Carbon','Soil pH','Soil CEC','Soil Nitrogen','Soil Clay','Soil Sand']
cropmask = ee.Image('COPERNICUS/Landcover/100m/Proba-V-C3/Global/2019').select('discrete_classification').eq(40)

Map = geemap.Map(center=[0, 0], zoom=2, Draw_export=True)

# Load CSS file content
with open('style.css', 'r') as css_file:
    css_content = css_file.read()
# Apply CSS styles
st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)

session_state = st.session_state
# Initialize variables
session_state.GenerateLink1 = False
session_state.GenerateLink2  = False
session_state.revisionLink =False
session_state.data = None
selected_variables = []

with st.sidebar:    
    st.image(logo)
    # st.experimental_rerun()
    st.write("## Upload AOI :gear:")
    data = st.file_uploader("Upload AOI Shapefile", type=["geojson","zip"])
       
    if data is not None:
        st.write("## Select Crop and Date: ")
        selected_Crop = st.sidebar.selectbox("Crop", crops)
        selected_Sdate = st.sidebar.date_input("Start",(datetime.date.today() - datetime.timedelta(days=10*365)))
        selected_Edate = st.sidebar.date_input("End")
   
tab1, tab2, tab3 = st.tabs([":orange[The App]", ":orange[How It Works]", ":orange[Data and Sources]"])

with tab2:
    # Read HTML file
    with open('HowTo.html', 'r') as file:
        html_content = file.read()
    # Display HTML content
    st.markdown(html_content, unsafe_allow_html=True)

with tab3:
    # Read HTML file
    with open('datasets.html', 'r') as file:
        html_content = file.read()
    # Display HTML content
    st.markdown(html_content, unsafe_allow_html=True)


with tab1:    
    if data is not None:
        try:
            file_path = save_uploaded_aoi(data, data.name)
            poly = gpd.read_file(file_path)
            geojson_geom = poly.geometry.__geo_interface__
            line = bbox(list(geojson.utils.coords(geojson_geom)))
            pairs = line.strip('()').split(',')
            coordinates = [tuple(map(float, pair.strip().split())) for pair in pairs]        
            # Calculate bounding box
            x_coords, y_coords = zip(*coordinates)
            xmin, xmax = min(x_coords), max(x_coords)
            ymin, ymax = min(y_coords), max(y_coords)
            # bounding box geometry
            bb = ee.Geometry.BBox(xmin, ymin, xmax, ymax)
            
            # Getting the centroid coordinates
            centroid_coords = ee.Geometry(bb).centroid(1).getInfo()['coordinates'][::-1]
    
            file_name = data.name
            aoiname=str(file_name.replace(".zip", ""))
    
            # Create map
            Map = geemap.Map(center=centroid_coords, zoom=8)
            Map.add_gdf(poly,  'AOI') 
            #Map.addLayer(bb, {}, 'Bounding Box')
            selected_Sdate1 = (datetime.date.today() - datetime.timedelta(days=10*365))
            selected_Edate1 = datetime.date.today() - datetime.timedelta(days=1*365)
    
            sdate = ee.Date.fromYMD(int(selected_Sdate1.strftime("%Y")),
                                int(selected_Sdate1.strftime("%-m")),
                                int(selected_Sdate1.strftime("%-d")))
            edate = ee.Date.fromYMD(int((selected_Edate1).strftime("%Y")),
                                int((selected_Edate1).strftime("%-m")),
                                int((selected_Edate1).strftime("%-d")))
    
            #recommended agronomic variables as per crop -to be updated
            if selected_Crop == "Maize":
                selected_variables=['Rainfall Days','Temperature Maximum',
            'Temperature Minimum', 'Elevation','Slope', 'Soil Organic Carbon','Soil pH','Soil CEC','Soil Nitrogen','Soil Clay','Soil Sand']
            elif selected_Crop == "Potato":
                selected_variables=varlist[0:5]
            elif selected_Crop == "Rice":
                selected_variables=varlist[1:8]
            elif selected_Crop == "Soybean":
                selected_variables=['Rainfall Days','Temperature Maximum',
            'Temperature Minimum', 'Soil Organic Carbon','Soil pH','Soil Nitrogen','Soil Clay','Soil Sand']
            else:
                selected_variables=varlist[0:6]
            
            #functions : data processing
            #load covariables
            prcSum = prcSum(selected_Sdate, selected_Edate,sdate, edate,bb)
            prcNrd = prcNrd(selected_Sdate, selected_Edate,sdate, edate,bb)
            Di = Di(selected_Sdate, selected_Edate,sdate, edate,bb)
            tmaxMax = tmaxMax(selected_Sdate, selected_Edate,sdate, edate,bb)
            tminMin = tminMin(selected_Sdate, selected_Edate,sdate,edate,bb)
            tmeanMean = tmeanMean(selected_Sdate, selected_Edate,sdate, edate,bb)
            zinc = zinc(bb)
            srtm = srtm(bb)
            slp=slp(bb)
            SOCmean=SOCmean(bb)
            pHmean=pHmean(bb)
            CECmean=CECmean(bb)
            Nmean=Nmean(bb)
            claymean=claymean(bb)
            sandmean=sandmean(bb)
            #Landscape Segmentation
            vectors = vectors(bb,selected_Sdate,selected_Edate,sdate,edate)
            # generate stack, training data
            stack = stackk(bb,selected_Sdate,selected_Edate,sdate,edate,selected_variables,prcSum, prcNrd,Di, tmaxMax ,tminMin ,tmeanMean,zinc,srtm, slp, SOCmean,pHmean,CECmean,Nmean,claymean,sandmean)
            training = get_training(bb,vectors,selected_variables,prcSum,  prcNrd, Di, tmaxMax ,tminMin ,tmeanMean,zinc,srtm, slp, SOCmean,pHmean,CECmean,Nmean,claymean,sandmean)
            x = get_x(training,selected_variables)
            
            #generate cluster output
            res,numClusters = get_res_xmeans(bb,training,selected_variables,x)
    
            #clip final ouput to aoi shape... otherwise expensive comp
            bb_clip = mapping(poly.geometry.unary_union)
            res = res.clip(bb_clip)   

            # numClusters = numClusters.getInfo()

            # def gen_colors(num_colors):
            #     random.seed(0) #ensure reproducibility
            #     random_colors = []
            #     for _ in range(num_colors):
            #         color = '#' + ''.join([format(random.randint(0,255),'02x')for _ in range(3)])
            #         random_colors.append(color)
            #     return random_colors
            #     #"#{:06x}".format(random.randint(0,0xFFFFFF))
            
            # palette = gen_colors(numClusters)
            # cluster_indices = list(range(numClusters))
            # style_res = {
            #     'bands': 'cluster',
            #     'min' :0,
            #     'max': numClusters - 1,
            #     'palette' : palette
            # }           
            
            Map.addLayer (res.randomVisualizer(), {}, 'Xmeans') 
            # Create a feature collection where each feature gets a cluster id, trials,... property
            outDiss= download_data(res,stack,bb,selected_variables,prcSum, prcNrd,Di, tmaxMax ,tminMin ,tmeanMean,zinc,srtm, slp, SOCmean,pHmean,CECmean,Nmean,claymean,sandmean)             
            Map.add_labels(
                outDiss,
                "cluster",
                font_size="12pt",
                font_color="black",
                font_family="arial",
                font_weight="bold"
            )
            # Function to add labels to features                    
            def add_labels(feature):       
                properties = feature['properties']
                cluster = properties['cluster']
                trials = properties['trials']
                label = f"Cluster: {cluster}    Trials:{trials}"  
                return folium.Popup(label, parse_html=True)

            for feature in outDiss.getInfo()['features']:
                geojson_feature = json.dumps(feature)
                folium.GeoJson(
                    geojson_feature,
                    style_function=lambda x: {'fillColor': '#ffff00', 'color': '#000000', 'weight': 2},
                    tooltip=folium.GeoJsonTooltip(fields=['cluster','trials'], labels=True),
                    popup=add_labels(feature),
                    name=''    #remove from layercontrol
                    ).add_to(Map)                            
              
            
        except Exception as e:
            st.error(e)
            #st.error("An error occurred: Try again. Ensure the AOI geometry is a polygon or rectangle. Very large or very small regions might not be processed either")
            
        try:
            st.sidebar.write("## Download: ")
            st.sidebar.markdown("Are you satisfied with the results? If yes, generate link below and Click 'Get Results' to download the results of unsupervised optimized clustering for use." )
            GenerateLink1 = st.sidebar.checkbox("Yes, Generate Download Link.")

            if GenerateLink1:                               
                st.sidebar.write("Click below to download file")
                current_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                gcs_path = f'data_{current_time}'
                task = ee.batch.Export.table.toCloudStorage(
                    collection=outDiss,
                    description='Export KML to GCS',
                    bucket='sfapp-eia',  # specify the name of your GCS bucket
                    fileNamePrefix = gcs_path,
                    fileFormat='KML'
                )     
                task.start()
                while task.active():
                    pass  
                #Get the export task status
                status = task.status()['state'] 
                if status == 'COMPLETED':
                    # Function to download file from GCS
                    def download_from_gcs(bucket_name, file_path, destination_path):
                        storage_client = storage.Client()
                        bucket = storage_client.bucket(bucket_name)
                        blob = bucket.blob(file_path)
                        blob.download_to_filename(destination_path)
                        return destination_path
                        
                    data_path = download_from_gcs('sfapp-eia', f'{gcs_path}.kml', "/tmp/f'{gcs_path}.kml'") 
                    def download_file(file_path):
                        with open(file_path, 'rb') as f:
                             kml_data = f.read()
                        return kml_data
                    kml_data=download_file(data_path)                    
                    
                    st.sidebar.download_button(
                        label='Get Results',
                        data= kml_data,
                        file_name=f'Data_{selected_Crop}_{current_time}.kml',
                        mime='application/kml'
                    )
            
       
        except Exception as e:
            st.error(e)
            # st.error("An error occurred: There is an issue with your file download. Try again") 

        try:
            revisionLink = st.sidebar.checkbox("No, Considering a revision of the clustering.")
            if revisionLink:                
                cluster_options =list(range( 1, 101))
                if numClusters in cluster_options:
                    cluster_options.remove(numClusters)
                cluster_options= [numClusters]+ cluster_options
                
                st.sidebar.write("## Considering a revision of the clustering: modify variables and/or the number of clusters ")
                variable_modification_options = st.sidebar.checkbox("Modify Variables", key="variable_modification")
                if variable_modification_options:
                    selected_variables = st.sidebar.multiselect(' ', varlist, default = selected_variables)
               #  if not variable_modification_options:
               #      #display default variables 
               #      v = str(selected_variables)
               #      var_clean_list = ", ".join(selected_variables)
               #      st.sidebar.write("Variables: ", var_clean_list)              
        
                cluster_modification_options = st.sidebar.checkbox("Modify Clusters", key="cluster_modification")        
                if not cluster_modification_options:
                    cluster_list = st.sidebar.write("Current Clusters: Optimal number of clusters used")
                    cluster_selection =numClusters
                if cluster_modification_options:
                    cluster_selection = st.sidebar.selectbox('Clusters', cluster_options,index=0)

            
                if variable_modification_options or cluster_modification_options:
                    training = get_training(bb,vectors,selected_variables,prcSum,  prcNrd, Di, tmaxMax ,tminMin ,tmeanMean,zinc,srtm, slp, SOCmean,pHmean,CECmean,Nmean,claymean,sandmean)
                    x = get_x(training,selected_variables)
                    res = get_res_kmeans(training,selected_variables,cluster_selection,x)
                    res = res.clip(bb_clip)
                    
                    Map = geemap.Map(center=[0, 0], zoom=2, Draw_export=True)
                    Map = geemap.Map(center=centroid_coords, zoom=8)
                    Map.add_gdf(poly,  'AOI') 

                    Map.addLayer (res.randomVisualizer(), {}, 'Kmeans')    
               # Create a feature collection where each feature gets a cluster property
                    outDiss= download_data(res,stack,bb,selected_variables,prcSum, prcNrd,Di, tmaxMax ,tminMin ,tmeanMean,zinc,srtm, slp, SOCmean,pHmean,CECmean,Nmean,claymean,sandmean)
                    
                    Map.add_labels(
                        outDiss,
                        "cluster",
                        font_size="12pt",
                        font_color="black",
                        font_family="arial",
                        font_weight="bold"
                    )
                    # Function to add labels to features                    
                    def add_labels(feature):       
                        properties = feature['properties']
                        cluster = properties['cluster']
                        trials = properties['trials']
                        label = f"Cluster: {cluster}    Trials:{trials}"  
                        return folium.Popup(label, parse_html=True)
        
                    for feature in outDiss.getInfo()['features']:
                        geojson_feature = json.dumps(feature)
                        folium.GeoJson(
                            geojson_feature,
                            style_function=lambda x: {'fillColor': '#ffff00', 'color': '#000000', 'weight': 2},
                            tooltip=folium.GeoJsonTooltip(fields=['cluster','trials'], labels=True),
                            popup=add_labels(feature),
                            name=''    #remove from layercontrol
                            ).add_to(Map)                            

                     
                    st.sidebar.write("## Download: ")
                    st.sidebar.markdown("Are you satisfied with the results? If yes, generate link below and Click 'Get Results' to download the results of the modified clustering for use." )
                    GenerateLink2 = st.sidebar.checkbox("Generate Download Link2")
                                    
                    if GenerateLink2:
                        st.sidebar.write("Click below to download the results of the modified clustering")
                        current_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                        gcs_path = f'data_{current_time}'
                        task = ee.batch.Export.table.toCloudStorage(
                            collection=outDiss,
                            description='Export KML to GCS',
                            bucket='sfapp-eia',  # specify the name of your GCS bucket
                            fileNamePrefix = gcs_path,
                            fileFormat='KML'
                        )     
                        task.start()
                        while task.active():
                            pass  
                        #Get the export task status
                        status = task.status()['state'] 
                        if status == 'COMPLETED':
                            # Function to download file from GCS
                            def download_from_gcs(bucket_name, file_path, destination_path):
                                storage_client = storage.Client()
                                bucket = storage_client.bucket(bucket_name)
                                blob = bucket.blob(file_path)
                                blob.download_to_filename(destination_path)
                                return destination_path
                                
                            data_path = download_from_gcs('sfapp-eia', f'{gcs_path}.kml', "/tmp/f'{gcs_path}.kml'") 
                            def download_file(file_path):
                                with open(file_path, 'rb') as f:
                                     kml_data = f.read()
                                return kml_data
                            kml_data=download_file(data_path)                            
                                
                            st.sidebar.download_button(
                                label='Get Results2',
                                data= kml_data,
                                file_name=f'Data_{selected_Crop}_{current_time}.kml',
                                mime='application/kml'
                            )
        except Exception as e:
            st.error(e)
            # st.error("An error occurred: There is an issue with your file download. Try again")  

    Map.to_streamlit(height=600)




        
with tab1:
    if data is not None:   
        st.markdown('<h4 style="color: rgb(69,45,34);">Clusters Details</h4>', unsafe_allow_html=True)
        st.markdown('<p style="color:#333;">The table below shows the different clusters generated with corresponding trial numbers to be allocated and the area of each cluster. </p>', unsafe_allow_html=True)
        st.markdown('<p style="color:#333;">Hint: Click on the column name to sort values in ascending or descending order. The download button appears on hover on the right corner of the table and can be used to download table data as .csv </p>', unsafe_allow_html=True)
        outDiss = download_data(res,stack,bb,selected_variables,prcSum, prcNrd,Di, tmaxMax ,tminMin ,tmeanMean,zinc,srtm, slp, SOCmean,pHmean,CECmean,Nmean,claymean,sandmean)
        cluster_data = outDiss.getInfo()
        trial_data=[]
        for feature in cluster_data['features']:
            cluster_id =feature['properties']['cluster']
            trials =feature['properties']['trials']
            area = feature['properties']['cAreaHa']
            trial_data.append({'Cluster ID':cluster_id, 'Trials': trials, 'Area (Ha)':area})

        st.dataframe(data=trial_data, use_container_width=True)


with tab1:
    if data is not None:         
        st.markdown('<h4 style="color: rgb(69,45,34);">Distribution of the Variables</h4>', unsafe_allow_html=True)
        st.markdown('<p style="color:#333;">The boxplots depicted below offer a visual snapshot of the distribution characteristics of the variables within the designated area of interest (AOI). The intricate details captured in these graphical representations provide insights into the central tendency, dispersion, and potential outliers within the dataset, aiding in a more nuanced understanding of the underlying data dynamics. Generating these boxplots may require additional computational time, especially when dealing with larger AOIs.</p>', unsafe_allow_html=True)
        st.markdown('<p style="color:#333;">Note: Please check the variability of data in the box plot. For instance, if there are only one or two values of the variable across the region, the box plot may appear as a line. If there is no data at all for a particular variable, no box plot will be displayed. You can adjust the variables accordingly based on this information.</p>', unsafe_allow_html=True) 
        properties_mapping = {
            'Rainfall Total': {'property': 'prcSum', 'unit': 'mm'},
            'Rainfall Days': {'property': 'prcNrd', 'unit': 'days'},
            'Rainfall Average': {'property': 'Di', 'unit': 'mm/day'},
            'Temperature Maximum': {'property': 'tmaxMax', 'unit': '°C'},
            'Temperature Minimum': {'property': 'tminMin', 'unit': '°C'},
            'Temperature Mean': {'property': 'tmeanMean', 'unit': '°C'},
            'Soil Zinc': {'property': 'zinc', 'unit':' ppmg'},
            'Elevation': {'property': 'srtm', 'unit': 'm'},
            'Slope': {'property': 'slp', 'unit': '%'},
            'Soil Organic Carbon': {'property': 'SOCmean', 'unit': 'dg/kg'},
            'Soil pH': {'property': 'pHmean', 'unit': ' '},
            'Soil CEC': {'property': 'CECmean', 'unit': 'mmol©/kg'},
            'Soil Nitrogen': {'property': 'Nmean', 'unit': 'g/kg'},
            'Soil Clay': {'property': 'claymean', 'unit': 'g/kg'} ,         
            'Soil Sand': {'property': 'sandmean', 'unit': 'g/kg'}  
        }   
       
  
        selected_variabless = [var for var in selected_variables if var in properties_mapping] 
       #  selected_variabless = list(properties_mapping.keys())           

        # Function to generate boxplot data
        def generate_boxplot(var_name):
            mapping = properties_mapping.get(var_name)
            if mapping:
                varInd = globals().get(mapping['property'])
                if varInd:
                    dta = varInd.clip(bb_clip)
                    data = dta.sample(numPixels=5000, region=bb_clip)
                    values = data.aggregate_array(dta.bandNames().getInfo()[0]).getInfo()
                    return values, mapping['unit']
            return None, None
    
        # Prepare subplot layout
        num_variables = len(selected_variabless)
        num_cols = 3
        num_rows = math.ceil(num_variables / num_cols)
         
        fig = make_subplots(rows=num_rows, cols=num_cols)         
        for i, var_name in enumerate(selected_variabless):
            if i < num_variables:
                values, unit = generate_boxplot(var_name)
                if values:
                    fig.add_trace(go.Box(y=values, name=f"{var_name}", boxmean='sd'),
                                  row=int(i / num_cols) + 1, col=i % num_cols + 1)
                    fig.update_yaxes(title_text=f"Values ({unit})", row=int(i / num_cols) + 1, col=i % num_cols + 1)
                else:
                    fig.add_trace(go.Box(y=[], name=f"{var_name}", boxmean='sd'),
                                  row=int(i / num_cols) + 1, col=i % num_cols + 1)
                    fig.update_yaxes(title_text="No data", row=int(i / num_cols) + 1, col=i % num_cols + 1)
                    fig.update_xaxes(title_text=f"{var_name}", row=int(i / num_cols) + 1, col=i % num_cols + 1)
    
        # Update layout and display plot
        fig.update_layout(height=1500, width=1000, title_text="Boxplots of Selected Variables", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

#End