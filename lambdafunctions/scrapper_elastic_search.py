import json
import boto3
from boto3.dynamodb.conditions import Key
import requests
import logging
from os import environ
from time import sleep
from urllib.parse import urlparse

from boto3 import Session

from opensearchpy import OpenSearch, Urllib3AWSV4SignerAuth, Urllib3HttpConnection

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('yelp-restaurants')
fn = getattr(requests, 'post')


def lambda_handler(event, context):
    # verbose logging
    logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)

    url = urlparse("https://search-restaurants-bw4t3h3pileb2cjaszkcatlfny.us-east-1.es.amazonaws.com")
    region = environ.get("AWS_REGION", "us-east-1")
    service = environ.get("SERVICE", "es")

    credentials = Session().get_credentials()

    auth = Urllib3AWSV4SignerAuth(credentials, region, service)

    client = OpenSearch(
        hosts=[{"host": url.netloc, "port": url.port or 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=Urllib3HttpConnection,
        timeout=30,
    )

    # TODO: remove when OpenSearch Serverless adds support for /
    if service == "es":
        info = client.info()
        # print(f"{info['version']['distribution']}: {info['version']['number']}")

    # create an index
    index = "restaurants"
    client.indices.create(index=index)
    # client.indices.delete(index=index)
    
    identifier=1
    resp = table.scan()
    while True:
        for item in resp['Items']:
            document = {"RestaurantID": item['id'], "Cuisine": item['cuisine']}
            client.index(index=index, body=document, id=identifier)
            identifier += 1
        
        if 'LastEvaluatedKey' in resp:
            resp = table.scan(
                ExclusiveStartKey=resp['LastEvaluatedKey']
            )
        else:
            break;
    
    return {
        'statusCode': 200,
        'body': json.dumps('Finished the job successfully')
    }