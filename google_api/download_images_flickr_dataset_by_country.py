# analysis and extraction of images by country 
# see https://github.com/NVlabs/ffhq-dataset
# 08.10.2022, TR

# The purpose of this python script is to download Flickr images (dataset: https://github.com/NVlabs/ffhq-dataset ) 
# from a Google Drive cloud.

# Some Code snippets from https://gist.github.com/henrych4/3a33018cbc27137b71fb4a28183eb8d1 are partly used.


# The script iterates over a local saved metadata file and analyse the attribute "country" within the metadata of all 70.000 images.
# All relevant countries will be defined in a list.
# All suitable images will be downloaded to a local directory. This script handles also the usage limitation of Google Drive API.
# By using a while-true loop the response status code will be checked. If it is not equal 200 (successful downloaded), it will repeat to request again 
# until the download succed. So, all images will be handled successfull within a long period of time.
# Important is the usage of a so-called "exponential backoff" for all further attempts of requests for the same image.

# time.sleep(2**number_attempts + random.uniform(0,1))

# Download on 8th of October 2022: 
# for six given countries 
# in total 432 images were downloaded in 9 hours 8 minutes.


# The download pattern is: 
# 30 successful requests to Google Drive API + 10 failed attempts with exponential backoff/ time out 
# (approx. 40 minutes until next successful download request)

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Import of python libraries:
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++


import pandas as pd
#import geopandas as gpd 
#from shapely.geometry import Point, Polygon, LineString
#import shapely
#import fiona

#import pyproj       # for transforming shapely geometry

import json

from random import randint, random

import time
from time import gmtime, strftime

#import numpy as np
#import matplotlib 
#import matplotlib.pyplot as plt
#import matplotlib.dates as mdates

import os
import sys
import math

import requests # for download
import shutil # to save it locally

import copy

import random

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++
# some functions for requesting Google Drive API
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++


# original source for this code snippets: 
# https://gist.github.com/henrych4/3a33018cbc27137b71fb4a28183eb8d1


def download_file_from_google_drive(id, destination):
    URL = "https://docs.google.com/uc?export=download"



    number_attempts = 0
    while True:

        session = requests.Session()
        number_attempts = number_attempts + 1
        response = session.get(URL, params = { 'id' : id }, stream = True)
        token = get_confirm_token(response)

        if token:
            params = { 'id' : id, 'confirm' : token }
            response = session.get(URL, params = params, stream = True)
        
        # catch request state of Google Drive API
        # print request state

        print(response.status_code)
        if response.status_code != 200:

            # if too many requests --> repeat by including exponential backoff!
            # exponential backoff/ timeout in case of failed requests
            time.sleep(2**number_attempts + random.uniform(0,1))
        else: 
            break

    save_response_content(response, destination)    

def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value

    return None

def save_response_content(response, destination):
    CHUNK_SIZE = 32768

    with open(destination, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++
# read metadata file as JSON data
print(str(strftime("%Y_%m_%d-%H_%M_%S", gmtime())) + ' - read metadata file as JSON data')
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++
with open(r'/path/to/metadata/json/file/ffhq-dataset-v2.json') as data_file:    
    data = json.load(data_file)  


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++
# set countries of interest
print(str(strftime("%Y_%m_%d-%H_%M_%S", gmtime())) + ' - set countries of interest')
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++

arr_list_countries = ['Country_1', 'Country_2', 'Country_3', 'Country_4', 'Country_5', 'Country_6'] # e.g. 'Germany'

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++
# set output path and create folder
print(str(strftime("%Y_%m_%d-%H_%M_%S", gmtime())) + ' - set output path and create folder')
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++

output_path = r'path/to/folder/for/output/'

# remove all existing data within the given output path
for filename in os.listdir(output_path):
    file_path = os.path.join(output_path, filename)
    try:
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
    except Exception as e:
        print('Failed to delete %s. Reason: %s' % (file_path, e))


for country in arr_list_countries:
    if not os.path.exists(os.path.join(output_path, country)):
        os.makedirs(os.path.join(output_path, country), mode=0o777) # enable permissions

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++
# start iteration over each image
print('***************************************')
print(str(strftime("%Y_%m_%d-%H_%M_%S", gmtime())) + ' - start iteration over each image')
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++   
print('length JSON array: ' + str(len(data)))

number_google_requests = 0

for i in range(0, len(data)):
    current_country = data[str(i)]['metadata']['country']

    #time.sleep(0.1)

    if current_country in arr_list_countries:
        # download image 1024x1024 px size (not thumbnail, not in_the_wild image version)
        download_url = data[str(i)]['image']['file_url']
        current_file_path = data[str(i)]['image']['file_path']
        current_filename = current_file_path.split("/")[-1]
        save_path = os.path.join(output_path, current_country, current_filename)
        
        # sleep 1 second
        #time.sleep(1)
        #r = requests.get(download_url, stream=True)
        
        dummy, file_id = download_url.split('=')

        # backoff because of limitations of Google Drive API

        number_google_requests = number_google_requests + 1
        #time.sleep(2**number_google_requests + random.uniform(0,1))

        if number_google_requests % 10 == 0:
            # every 18.000 requests
            print('******************')
            print('sleep 100 seconds --> because of usage limit')
            time.sleep(100)

        print(str(i) + ' - ' + str(number_google_requests) + ' - Google Drive ID: ' + str(file_id) + ' - save path: ' + str(save_path))
        
        download_file_from_google_drive(file_id, save_path)


        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # save suitable metadata file for downloaded image

        # set JSON part 
        current_json_data = copy.deepcopy(data[str(i)])
        image_number, image_suffix = current_filename.split('.')
        new_file_name = image_number + '_metadata.json'
        output_path_metadata = os.path.join(output_path, current_country, new_file_name)

        with open(output_path_metadata, 'w') as outfile:
            json.dump(current_json_data, outfile)



        
        del download_url, save_path, current_filename
        del current_file_path, current_json_data, image_number, image_suffix, new_file_name, output_path_metadata
        #del r

        # Usage limits of Google Drive API
        # if too manye requests in to less time --> empty response
        # https://developers.google.com/drive/api/guides/limits
        if i % 18000 == 0:
            # every 18.000 requests
            print('******************')
            print('sleep 100 seconds --> because of usage limit')
            time.sleep(100)



    del current_country



# +++++++++++++++++++++++++++++++++++++++++++++++++++++++
# finish
print('***************************************')
print(str(strftime("%Y_%m_%d-%H_%M_%S", gmtime())) + ' - finish')
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++  
