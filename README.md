<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" >
    <meta name="generator" content="pandoc" >
    <meta http-equiv="X-UA-Compatible" content="IE=EDGE" >
    
</head>
<body>
    
<div class="container-fluid main-container"> 
    <div id="excellence-in-agronomy-eia-initiative---sampling-frames-for-validation" class="section level1">
        <h1>Excellence in Agronomy (EiA) initiative - Sampling Frames for Validation</h1>
        <p style="color: #333;">This tool provides users with a solution to select relevant areas and
        locations where they can conduct the validation trials for their Minimum
        Viable Products (MVP’s). The tool guides the user through a set of steps
        that will allow them to make decisions on what is the most relevant set
        of environmental clusters that can help reduce variance due to
        environmental conditions, making the results of their trials more
        representative for their target area (AOI).
        </p>
        <img src="https://live.staticflickr.com/65535/53788703449_12d0b1bc25_h.jpg" alt=""></img>
        <div id="to-provide-a-bit-more-explanation-of-the-tool-and-links-to-additional-documentation" class="section level5">
            <h5>(to provide a bit more explanation of the tool and links to additional documentation)</h5>
        </div> 
    </div>
    <div id="define-the-trial-conditions" class="section level2" >
            <h2 style="color: rgb(65,45,34);">Define the trial conditions:</h2>
            <p style="color: #333;">On the left-side panel of the tool, the user is initially provided
                with a set of options to define the trial conditions in which they want
                to run validations.</p>
            <div id="define-the-target-region-or-area-of-interest-aoi" class="section level3">
                <h3>1. Define the target region or Area Of Interest (AOI)</h3>
                <p style="color: #333;">The user will need to provide the file in .shp or .geojson formats to
                    set the AOI where the trials will be conducted. This will define the tool for which to process the different environmental units in
                    the AOI.</p>
                <div > <img src="assets/upload_aoi.GIF"  alt="">  </div>
                <p style="color: #333;">Alternatively, the user could manually draw a shape on the map that
                    defines the region of interest.</p>
                <div> <img src="https://live.staticflickr.com/video/53788773123/e886b8ae42/1080p.mp4?s=eyJpIjo1Mzc4ODc3MzEyMywiZSI6MTcxODI4ODUwMiwicyI6IjAyYjNjMTIwMDdhYzQyZTMyNjg2MTI3ZWI4NzQwZDJiNmVlMmU3Y2YiLCJ2IjoxfQ"  alt="">  </div>
                <p style="color: #333;"><strong>Note</strong>: The size of the area has a limit of XXX km2.Consider this, as the tool will not work for 
                    very large areas. In case you need to run the tool for a very large AOI, you can 
                    contact <a href="mailto:xxxx.xxxxx@cgiar.org" class="email">xxxx.xxxxx@cgiar.org</a></p>
                </div>
        <div id="indicate-the-main-crop" class="section level3">
                <h3>2. Indicate the main crop</h3>
                <p style="color: #333;">In this step, the user will define the main crop that the trials are targeting to validate. 
                    This is done to select a set of relevant environmental variables that are considered most relevant by agronomists. 
                    The crops available, together with the list of associated variables are indicated in the table below:</p>
                <p style="color: #333;">[Table with crops + variables]</p>
        </div>
        <div id="define-the-seasonality" class="section level3">
                <h3>3. Define the seasonality</h3>
                <p style="color: #333;">Seasonal conditions affect how environments might be clustered within the AOI, thus affecting the results 
                    of the trials and how the crop performs. The tool requires that the user indicates the seasonality (start month and end month) 
                    when the trials will be conducted.</p>
                </div>
        <div id="optimal-clusters-for-the-trials" class="section level2">
            <h2 style="color: rgb(65,45,34);">Optimal clusters for the trials:</h2>
            <p style="color: #333;">After defining the trial conditions, the user will be provided with a first result of the optimal number of 
                clusters in the AOI. These indicates which are the environmentally distinct areas specific for the crop the trials are targeting.</p>
            <p style="color: #333;">[<em>To be added… The user can view this clusters and also see what is the proportion of trials that should be 
                set-up in each cluster to get a balanced sample size that improves representativeness of the results.</em>]</p>
            <p style="color: #333;">[<em>Below the map the user can see the boxplots for the different variables included for 
                the crops and which are the distributions (in boxplots) of the variables within each cluster.</em>]</p>
            <p style="color: #333;">If the user is satisfied with the results, these can be exported to
                further investigation or discussion with the team. Click the “Get Results” button to download to your computer.</p>
            </div>
        <div id="user-defined-number-of-clusters" class="section level2">
            <h2 style="color: rgb(65,45,34);">User-defined number of clusters</h2>
            <p style="color: #333;">In case the user does not agree with the results, is possible to navigate to the next step, 
                where the user will be able to create a more tailored set of clusters. <strong>This optional step strongly influences
                    the results.</strong></p>
            <div id="number-of-clusters" class="section level3">
                <h3>4. Number of clusters</h3>
                <p style="color: #333;">If for some reason the optimal number of clusters defined by the dry-run of the tool is not desirable, 
                    the user may indicate what would be a more adequate number that fits their knowledge of the area or the logistical constraints. 
                    Please, [select a number from the drop-down / indicate a number].</p>
                </div>
            <div id="relevant-environmental-variables" class="section level3">
                <h3>5. Relevant environmental variables</h3>
                <p  style="color: #333;">At this point, the user may also decide which are the most relevant environmental variables that may 
                    influence the trials or that are of specific focus in the validation. For example, an MVP might be focusing on drought-resistant
                    varieties in rainfed wheat, and therefore rainfall might be the most important environmental variable to define the
                    different environmental clusters.</p>
                <p  style="color: #333;">The user should remove the variables from the box and only leave those that are relevant for the validation.</p>
                <div> <img src="assets/selectvars.GIF" alt="">  </div>
                <p  style="color: #333;">The user can test several combinations of variables and number of clusters and see the effects in the clusters 
                    and variable distributions until an acceptable result is obtained. Once satisfied, the user can export the user-defined clusters by 
                    clicking the “Get Results” button to download to the computer.</p>
                </div>
            </div>
            </div>
</div>    
</body>
</html>






