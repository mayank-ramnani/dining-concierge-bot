#!/usr/bin/env python
# coding: utf-8

# In[1]:


import json
import boto3
import datetime
import requests
from decimal import *
from time import sleep
import os

AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
YELP_API_KEY = os.environ['YELP_API_KEY']
# In[2]:


client = boto3.resource(service_name='dynamodb',
                          aws_access_key_id=AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                          region_name="us-east-1",
                         )
table = client.Table('yelp-restaurants')


# In[3]:

restaurants = {}
def addItems(data, cuisine):
   global restaurants
   with table.batch_writer() as batch:
        for rec in data:
            try:
                if rec["alias"] in restaurants:
                    continue;
                rec["Business ID"] = str(rec["id"])
                rec["rating"] = Decimal(str(rec["rating"]))
                restaurants[rec["alias"]] = 0
                rec['cuisine'] = cuisine
                rec['insertedAtTimestamp'] = str(datetime.datetime.now())
                rec["coordinates"]["latitude"] = Decimal(str(rec["coordinates"]["latitude"]))
                rec["coordinates"]["longitude"] = Decimal(str(rec["coordinates"]["longitude"]))
                rec['address'] = rec['location']['display_address']
                rec.pop("distance", None)
                rec.pop("location", None)
                rec.pop("transactions", None)
                rec.pop("display_phone", None)
                rec.pop("categories", None)
                if rec["phone"] == "":
                    rec.pop("phone", None)
                if rec["image_url"] == "":
                    rec.pop("image_url", None)

                # print(rec)
                batch.put_item(Item=rec)
                sleep(0.001)
            except Exception as e:
                print(e)
                print(rec)



cuisines = ['indian', 'thai', 'mediterranean', 'chinese', 'italian']
headers = {'Authorization': 'Bearer '+YELP_API_KEY}

DEFAULT_LOCATION = 'Manhattan'

def lambda_handler(event, context):
    for cuisine in cuisines:
        print(cuisine)
        for i in range(0, 1000, 50):
            params = {'location': DEFAULT_LOCATION, 'offset': i, 'limit': 50, 'term': cuisine + " restaurants"}
            response = requests.get("https://api.yelp.com/v3/businesses/search", headers = headers, params=params)
            js = response.json()
            #print(js["businesses"])
            addItems(js["businesses"], cuisine)