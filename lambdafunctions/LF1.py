import json
import dateutil.parser
import datetime
import time
import os
import math
import random
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

SQS = boto3.client("sqs")

# output format: https://docs.aws.amazon.com/lexv2/latest/dg/lambda-response-format.html
def close(session_attributes, intent_name, fulfillment_state):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close'
            },
        'intent': {
            'name': intent_name,
            'state': fulfillment_state
            # 'message': message
        }
    }

    return {"sessionState": response}

def is_valid_cuisine(cuisine):
    if not (cuisine == "indian" or cuisine == "thai" or cuisine == "mediterranean" or cuisine == "italian" or cuisine == "chinese"):
        return False
    else:
        return True


""" --- Functions that control the bot's behavior --- """
def give_dining_suggestions(request):
    output_session_attributes = request['sessionAttributes'] if request['sessionAttributes'] is not None else {}
    
    dining_city = request['intent']['slots']['DiningCity']['value']['interpretedValue']
    dining_cuisine = request['intent']['slots']['CuisineType']['value']['interpretedValue']
    dining_time = request['intent']['slots']['DiningTime']['value']['interpretedValue']
    people_count = request['intent']['slots']['PeopleCount']['value']['interpretedValue']
    user_email = request['intent']['slots']['UserEmail']['value']['interpretedValue']

    if not (is_valid_cuisine(dining_cuisine)):
        return close(
        output_session_attributes,
        'DiningSuggestionsIntent',
        'Failed'
    )

    logger.debug('send email here')
    
    email_request = {}
    # email_request["place"] = "New York"
    # email_request["cuisine"] = "Indian"
    # email_request["time"] = "16:00"
    # email_request["people_count"] = 4
    # email_request["email"] = "x@y.com"

    email_request["place"] = dining_city
    email_request["cuisine"] = dining_cuisine
    email_request["time"] = dining_time
    email_request["people_count"] = people_count
    email_request["email"] = user_email


    resp = SQS.send_message(
            QueueUrl="https://sqs.us-east-2.amazonaws.com/381492225860/test-queue", 
            MessageBody=json.dumps(email_request)
        )

    logger.debug('sent message to sqs: ')
    logger.debug('{}'.format(json.dumps(email_request)))

    return close(
        output_session_attributes,
        'DiningSuggestionsIntent',
        'Fulfilled'
    )


def handle_greeting_intent(request):
    print(request)

""" --- Intents --- """


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """
    logger.debug(json.dumps(intent_request))

    intent_name = intent_request['sessionState']['intent']['name']
    logger.debug('dispatch intent is={}'.format(intent_name))
    # Dispatch to your bot's intent handlers
    if intent_name == 'GreetingIntent':
        return handle_greeting_intent(intent_request['sessionState'])
    if intent_name == 'DiningSuggestionsIntent':
        return give_dining_suggestions(intent_request['sessionState'])
    else:
        raise Exception('Intent with name ' + intent_name + ' not supported')


""" --- Main handler --- """
def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    logger.debug('Started the bot')
    os.environ['TZ'] = 'America/New_York'
    time.tzset()

    return dispatch(event)