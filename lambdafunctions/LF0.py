import boto3
import json
import logging
from os import environ

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    client = boto3.client('lexv2-runtime')
    response = client.recognize_text(
        botId=environ["BOT_ID"],
        botAliasId=environ["BOT_ALIAS_ID"],
        localeId="en_US",
        sessionId=event['SessionId'],
        text=event['UserInput'])
    
    # Extract the response from the Lex runtime API response
    lex_response = response['messages'][0]['content']
    # Return the Lex response
    return {
        'statusCode': 200,
        'body': json.dumps({'message': lex_response})
    }