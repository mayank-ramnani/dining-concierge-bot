import logging
from os import environ
from time import sleep
from urllib.parse import urlparse
import boto3
from boto3 import Session
import json
from boto3.dynamodb.conditions import Key

from opensearchpy import OpenSearch, Urllib3AWSV4SignerAuth, Urllib3HttpConnection
import smtplib

from string import Template

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

FROM_ADDRESS = environ['FROM_ADDRESS']

HOST='email-smtp.us-east-1.amazonaws.com'
PORT=587
SMTP_USERNAME=environ['SMTP_USERNAME']
SMTP_PASSWORD=environ['SMTP_PASSWORD']

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('yelp-restaurants')
SQS = boto3.client("sqs")
sqs_url = 'https://sqs.us-east-1.amazonaws.com/381492225860/test-queue'

# verbose logging
logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)
es_url = urlparse("https://search-restaurants-bw4t3h3pileb2cjaszkcatlfny.us-east-1.es.amazonaws.com")
region = environ.get("AWS_REGION", "us-east-1")
service = environ.get("SERVICE", "es")
credentials = Session().get_credentials()
auth = Urllib3AWSV4SignerAuth(credentials, region, service)
es_client = OpenSearch(
    hosts=[{"host": es_url.netloc, "port": es_url.port or 443}],
    http_auth=auth,
    use_ssl=True,
    verify_certs=True,
    connection_class=Urllib3HttpConnection,
    timeout=30,
)
    
def getSQSMsg():
    response = SQS.receive_message(
        QueueUrl=sqs_url, 
        AttributeNames=['SentTimestamp'],
        MessageAttributeNames=['All'],
        VisibilityTimeout=0,
        WaitTimeSeconds=0
    )
    try:
        message = response['Messages'][0]
        if message is None:
            logger.debug("Empty message")
            return None
    except KeyError:
        logger.debug("No message in the queue")
        return None
    message = response['Messages'][0]
    logger.debug('Received message: %s' % response)
    return message
    
def deleteSQSMsg(message):
    if message is None:
        return None
    SQS.delete_message(
        QueueUrl=sqs_url,
        ReceiptHandle=message['ReceiptHandle']
    )
    logger.debug('Deleted message: %s' % message)
    return "message deleted from SQS"
    
def fetchRestaurant(message):
    if message is None:
        return None
    data = json.loads(message['Body'])
    email = data['email']
    place = data['place']
    cuisine = data['cuisine']
    people_count = data['people_count']
    time = data['time']
    index = "restaurants"
    results = es_client.search(body={"query": {"match": {"Cuisine": cuisine}}})
    res = results['hits']['hits'][0]['_source']['RestaurantID']
    dbRes = table.query(KeyConditionExpression=Key('id').eq(res))
    return(dbRes)
    
def formatEmail(restaurant):
    if restaurant is None:
        return None
    # return restaurant
    # return(restaurant['Items'][0].keys())
    # price = str(restaurant['Items'][0]['price'])
    # restaurant_phone = str(restaurant['Items'][0]['phone'])
    price = "$$"
    restaurant_phone = "2186771329"
    addr = str(restaurant['Items'][0]['address'])
    # return "hello"
    # if 'price' in restaurant['Items'][0].keys():
    #     price = str(restaurant['Items'][0]['price'])
    # else:
    #     price = 'NA'
    # if 'phone' in restaurant['Items'][0].keys():
    #     restaurant_phone = str(restaurant['Items'][0]['phone'])
    # else:
    #     restaurant_phone = 'NA'
    # addr = str(restaurant['Items'][0]['address'])
    for char in "'u[]":
        addr = addr.replace(char, '')
    formatted_message = 'The best deal for you: Restaurant Name: ' + restaurant['Items'][0][
        'name'] + ', Price: ' + price  + ', Phone: ' + restaurant_phone + ', Address: ' + addr
    return formatted_message
    

def send_email_smtp(message, sqs_message):
    if sqs_message is None:
        return None
    if message is None:
        return None

    # set up the SMTP server
    s = smtplib.SMTP(host=HOST, port=PORT, timeout=30)
    print("init")
    print(s)
    s.starttls()
    print("started tls")
    s.login(SMTP_USERNAME, SMTP_PASSWORD)
    print("logged in")

    msg = MIMEMultipart()       # create a message
    # message = "hello world 2"

    # # Prints out the message body for our sake
    # print(message)
    
    # to_addr = "mr7172@nyu.edu"
    body = json.loads(sqs_message['Body'])
    to_addr = body['email']
    print(to_addr)

    # setup the parameters of the message
    msg['From']=FROM_ADDRESS
    msg['To']=to_addr
    msg['Subject']="This is from lambda"
    
    # add in the message body
    msg.attach(MIMEText(message, 'plain'))
        
    # send the message via the server set up earlier.
    s.send_message(msg)
    del msg
    
    # Terminate the SMTP session and close the connection
    s.quit()    

def lambda_handler(event, context):
    sqs_message = getSQSMsg()
    restaurant = fetchRestaurant(sqs_message)
    formatted_message = formatEmail(restaurant)
    send_email_smtp(formatted_message, sqs_message)
    deleteSQSMsg(sqs_message)

    return {
        'statusCode': 200,
        'body': json.dumps("LF2 executed succesfully")
    }