import ee
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
from eefun import *

# # # # Need to refresh token every week
# ee.Authenticate()
# ee.Initialize(project='midyear-button-379815')


logo = "assets/EiA_logo.png"
logo2 = "assets/EiA_logo2.png"
# Wide app layout
st.set_page_config(layout="wide", page_title="Sampling Framework", page_icon=logo2)
st.header(":green[Sampling Framework]")
#st.markdown('<h1 style="color: rgb(85,176,71);">Sampling Framework</h1>', unsafe_allow_html=True)
        

crops = ["Maize", "Potato", "Cassava","Rice", "Wheat", "Soybean", "Teff", "Sorghum" ]
varlist = ['Rainfall Total', 'Rainfall Days','Rainfall Average','Temperature Maximum',
            'Temperature Minimum','Temperature Mean','Soil Zinc', 'Elevation']
cropmask = ee.Image('COPERNICUS/Landcover/100m/Proba-V-C3/Global/2019').select('discrete_classification').eq(40)



Map = geemap.Map(center=[0, 0], zoom=2, Draw_export=True)

# Initialize variables
show_clusters = False
downloaderr_input  = False
proces_input =False
show_process2 = True
cluster_selection = 1
var_selection = False
selected_variables = []

# Load CSS file content
with open('style.css', 'r') as css_file:
    css_content = css_file.read()

# Apply CSS styles
st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)


with st.sidebar:    
    st.image(logo)
        
    st.write("## Upload AOI :gear:")
    data = st.file_uploader("Upload AOI Shapefile", type=["geojson","zip"])
    
    if data is not None:
        st.write("## Select Crop and Date: ")
        selected_Crop = st.sidebar.selectbox("Crop", crops)
        selected_Sdate = st.sidebar.date_input("Start",(datetime.date.today() - datetime.timedelta(days=10*365)))
        selected_Edate = st.sidebar.date_input("End")
               
tab1, tab2 = st.tabs([":orange[The App]", ":orange[How It Works]"])

with tab2:
    #st.write("How It Works") 
    # Read HTML file
    with open('HowTo.html', 'r') as file:
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
            selected_Sdate1 = (datetime.date.today() - datetime.timedelta(days=5*365))
            selected_Edate1 = datetime.date.today()
    
            sdate = ee.Date.fromYMD(int(selected_Sdate1.strftime("%Y")),
                                int(selected_Sdate1.strftime("%-m")),
                                int(selected_Sdate1.strftime("%-d")))
            edate = ee.Date.fromYMD(int((selected_Edate1).strftime("%Y")),
                                int((selected_Edate1).strftime("%-m")),
                                int((selected_Edate1).strftime("%-d")))
    
            #reccommended agronomic variables as per crop
            if selected_Crop == "Maize":
                selected_variables=varlist
            elif selected_Crop == "Potato":
                selected_variables=varlist[0:5]
            elif selected_Crop == "Beans":
                selected_variables=varlist[2:7]
            else:
                selected_variables=varlist
            
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
            #Landscape Segmentation
            vectors = vectors(bb,selected_Sdate,selected_Edate,sdate,edate)
            # generate stack, training data
            stack = stackk(bb,selected_Sdate,selected_Edate,sdate,edate,selected_variables,prcSum, prcNrd,Di, tmaxMax ,tminMin ,tmeanMean,zinc,srtm)
            training = get_training(bb,vectors,selected_variables,prcSum,  prcNrd, Di, tmaxMax ,tminMin ,tmeanMean,zinc,srtm)
            x = get_x(training,selected_variables)
            
            #generate cluster output
            res = get_res_xmeans(training,selected_variables,x)
    
            #clip final ouput to aoi shape... otherwise expensive comp
            bb_clip = mapping(poly.geometry.unary_union)
            res = res.clip(bb_clip)        
    
            Map.addLayer (res.randomVisualizer(), {}, 'Xmeans')  
        except Exception as e:
            st.error(e)
            #st.error("An error occurred: Try again. Ensure the AOI geometry is a polygon or rectangle. Very large or very small regions might not be processed either")
            
        try:
            st.sidebar.write("## Download: ")
            st.sidebar.markdown("Are you satisfied with the results? If yes, generate link below and Click 'Get Results' to download the results of unsupervised optimized clustering for use." )

            if st.sidebar.checkbox("Generate Download Link."):
                outDiss = download_data(res,stack,bb,selected_variables,prcSum, prcNrd,Di, tmaxMax ,tminMin ,tmeanMean,zinc,srtm)
                st.sidebar.write("Click below to download file")
                current_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                gcs_path = f'data_{current_time}'
                task = ee.batch.Export.table.toCloudStorage(
                    collection=outDiss,
                    description='Export KML to GCS',
                    bucket='eia2030',  # specify the name of your GCS bucket
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
                        
                    data_path = download_from_gcs('eia2030', f'{gcs_path}.kml', "/tmp/f'{gcs_path}.kml'") 
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
            # numClusters = outDiss.size()
            numClusters = get_numClusters(bb,training,selected_variables,x)     
            #st.write(numClusters.getInfo())
            numClusters = numClusters.getInfo()
            cluster_options =list(range( 1, 101))
            if numClusters in cluster_options:
                cluster_options.remove(numClusters)
            cluster_options= [numClusters]+ cluster_options
            
            st.sidebar.write("## Considering a revision of the clustering: modify variables and/or the number of clusters ")
            variable_modification_options = st.sidebar.checkbox("Modify Variables", key="variable_modification")
            if variable_modification_options:
                selected_variables = st.sidebar.multiselect('Current Variables', varlist, default = selected_variables)
            if not variable_modification_options:
                #display default variables 
                v = str(selected_variables)
                var_clean_list = ", ".join(selected_variables)
                st.sidebar.write("Variables: ", var_clean_list)              
    
            cluster_modification_options = st.sidebar.checkbox("Modify Clusters", key="cluster_modification")        
            if not cluster_modification_options:
                cluster_list = st.sidebar.write("Current Clusters: Optimal number of clusters used")
            if cluster_modification_options:
                cluster_selection = st.sidebar.selectbox('Clusters', cluster_options,index=0)
                
    
                	

        except Exception as e:
            st.error(e)
            #st.error("An error occurred: Please try again. ")
        
            
       
        try:
            if variable_modification_options or cluster_modification_options:
                res = get_res_kmeans(training,selected_variables,cluster_selection,x)
                res = res.clip(bb_clip)
        
                Map.addLayer (res.randomVisualizer(), {}, 'Kmeans')
            
                st.sidebar.write("## Download: ")
                st.sidebar.markdown("Are you satisfied with the results? If yes, generate link below and Click 'Get Results' to download the results of the modified clustering for use." )
                                
                if st.sidebar.checkbox("Generate Download Link2"):
                    outDiss = download_data(res,stack,bb,selected_variables,prcSum, prcNrd,Di, tmaxMax ,tminMin ,tmeanMean,zinc,srtm)
                    st.sidebar.write("Click below to download the results of the modified clustering")
                    current_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                    gcs_path = f'data_{current_time}'
                    task = ee.batch.Export.table.toCloudStorage(
                        collection=outDiss,
                        description='Export KML to GCS',
                        bucket='eia2030',  # specify the name of your GCS bucket
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
                            
                        data_path = download_from_gcs('eia2030', f'{gcs_path}.kml', "/tmp/f'{gcs_path}.kml'") 
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
        #st.markdown("#### Distribution of the Variables ")
        st.markdown('<h4 style="color: rgb(69,45,34);">Distribution of the Variables</h4>', unsafe_allow_html=True)
        st.markdown('<p style= "color:#333;">The boxplots depicted below offer a visual snapshot of the distribution characteristics of the variables within the designated area of interest (AOI). The intricate details captured in these graphical representations provide insights into the central tendency, dispersion, and potential outliers within the dataset, aiding in a more nuanced understanding of the underlying data dynamics. Generating these boxplots may require additional computational time, especially when dealing with larger AOIs.</p>', unsafe_allow_html=True)
        # try:
        #bb_clip = ee.Geometry.Polygon(bb_clip.geometry().bounds())
        # bb_shp = ee.Geometry.Rectangle([xmin, ymin, xmax, ymax])
        # aoi_area = bb_shp.area().getInfo()   
               
        properties_mapping = {
            'Rainfall Total': 'prcSum',
            'Rainfall Days': 'prcNrd',
            'Rainfall Average': 'Di',
            'Temperature Maximum': 'tmaxMax',
            'Temperature Minimum': 'tminMin',
            'Temperature Mean': 'tmeanMean',
            'Soil Zinc': 'zinc',
            'Elevation': 'srtm'
            }
        i_variables = [properties_mapping[var] for var in selected_variables if var in properties_mapping]


        # Function to generate boxplot as bytes
        def generate_boxplot(var_name):
            # Get property name from mapping
            varInd = properties_mapping.get(var_name)
            if varInd:  # Check if property exists
                varInd = globals()[varInd]
                # Clip image to region of interest (if needed)
                dta = varInd.clip(bb_clip)
                
                # # Get the nominal scale of the projection
                # scale = dta.projection().nominalScale().getInfo()
                # scale_value = math.sqrt(aoi_area) / scale   
                # scale_value = min(scale_value, 1000)  # Adjust maximum scale value as needed
                # Sample the image data
                #data = dta.sample(scale=scale_value, factor=0.4, region=bb_clip)
                data = dta.sample(numPixels=5000, region=bb_clip)
                values = data.aggregate_array(dta.bandNames().getInfo()[0]).getInfo()  # Aggregate values
                #fig = go.Figure(data=[go.Box(y=values)])
                return values
                # # Plot boxplot
                # fig, ax = plt.subplots(figsize=(8, 6))
                # ax.boxplot(values)
                # ax.set_title(var_name)  # Add title with variable name
                                    
                # # Convert plot to bytes
                # buf = io.BytesIO()
                # plt.savefig(buf, format='png')
                # plt.close(fig)
                # buf.seek(0)
                # return buf.getvalue()
            else:
                return None
        # Calculate number of rows and columns for subplot layout
        num_variables = len(selected_variables)
        num_cols = 3  # Number of columns
        num_rows = math.ceil(num_variables / num_cols)  # Number of rows

        fig = make_subplots(rows=int(num_variables/3)+1, cols=3)

        for i, var_name in enumerate(selected_variables):
            if i < num_variables:
                var_name = selected_variables[i]
                plot_bytes = generate_boxplot(var_name)
                if plot_bytes:
                    fig.add_trace(go.Box(y=plot_bytes, name=f"{var_name}", boxmean='sd'),
                          row=int(i/3)+1, col=i%3+1)
                    #fig.update_xaxes(title_text=var_name, row=int(i/3)+1, col=i%3+1)
                    fig.update_yaxes(title_text="Values", row=int(i/3)+1, col=i%3+1)

        # Update layout
        fig.update_layout(height=1500, width=1000, title_text="Boxplots of Selected Variables",showlegend=False)
        
        # Display the plot
        st.plotly_chart(fig, use_container_width=True)

