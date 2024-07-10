# First stage: Base setup with Miniconda and required installations
FROM python:3.9-slim as base

# Update package lists and install necessary packages
RUN apt-get update && \
    apt-get install -y wget curl gnupg && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables for Miniconda
ENV PATH="/root/miniconda3/bin:${PATH}"

# Install Miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    mkdir /root/.conda && \
    bash Miniconda3-latest-Linux-x86_64.sh -b && \
    rm -f Miniconda3-latest-Linux-x86_64.sh

# Install Earth Engine API and create a conda environment
RUN conda install -y -c conda-forge earthengine-api && \
    conda create --name gee python

# Install Mamba and Geemap
RUN conda install -y -c conda-forge mamba  && \
    mamba install -y -c conda-forge geemap

# Install Python dependencies
RUN pip3 install streamlit geojson geopandas datetime shapely matplotlib plotly python-dotenv

# Second stage: Final image with only the necessary components
FROM python:3.9-slim

# Copy Miniconda from the base stage
COPY --from=base /root/miniconda3 /root/miniconda3
COPY --from=base /root/.conda /root/.conda

# Set environment variables for Miniconda
ENV PATH="/root/miniconda3/bin:${PATH}"

# Install necessary packages for Google Cloud SDK
RUN apt-get update && \
    apt-get install -y wget curl gnupg && \
    rm -rf /var/lib/apt/lists/*

# Install Google Cloud SDK
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" \
    | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - && \
    apt-get update && \
    apt-get install -y google-cloud-sdk

# Set environment variables for Google Cloud SDK
ENV PATH="/usr/lib/google-cloud-sdk/bin:${PATH}"

# Set the Google Application Credentials environment variable
ENV GOOGLE_APPLICATION_CREDENTIALS="/var/secrets/google/sampling-frames-iita-a80b3e765388.json"


# Copy the working directory contents from the base stage
WORKDIR /SFApp
COPY . .

# Expose Streamlit default port
EXPOSE 8501

# Healthcheck
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Specify the entry point
ENTRYPOINT ["streamlit", "run", "SFapp.py", "--server.port=8501"]
