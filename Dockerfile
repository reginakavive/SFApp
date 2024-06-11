FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y wget curl
    
ENV PATH="/root/miniconda3/bin:${PATH}"
ARG PATH="/root/miniconda3/bin:${PATH}"

RUN apt-get update
   
RUN apt-get install -y wget && rm -rf /var/lib/apt/lists/*
  
RUN wget \
    https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    mkdir /root/.conda && \
    bash Miniconda3-latest-Linux-x86_64.sh -b && \
    rm -f Miniconda3-latest-Linux-x86_64.sh 

WORKDIR ~/SFApp

COPY SFApp/ .

RUN conda install -y -c conda-forge earthengine-api && \
    conda create --name gee python

RUN conda install -y -c conda-forge mamba  && \
    mamba install -y -c conda-forge geemap

RUN pip3 install streamlit \
    geojson \
    geopandas \
    datetime \
    shapely \
    matplotlib \
    # math \
    # io \
    plotly

RUN curl -sSL https://sdk.cloud.google.com | bash
