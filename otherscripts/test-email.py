import smtplib

from string import Template

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

FROM_ADDRESS = 'mayankr99+aws@gmail.com'

HOST='email-smtp.us-east-1.amazonaws.com'
PORT=25
SMTP_USERNAME=""
SMTP_PASSWORD=""

# client = boto3.client('ses', region_name='us-east-1')

# def send_mail(from_addr, to_addr, body_content):
#     response = client.send_email(
#     Destination={
#         'ToAddresses': [to_addr]
#     },
#     Message={
#         'Body': {
#             'Text': {
#                 'Charset': 'UTF-8',
#                 'Data': body_content,
#             }
#         },
#         'Subject': {
#             'Charset': 'UTF-8',
#             'Data': 'Test email',
#         },
#     },
#     Source=from_addr
#     )
    
#     print(response)
#     return {
#         'statusCode': 200,
#         'body': json.dumps("Email Sent Successfully. MessageId is: " + response['MessageId'])
#     }

# def read_template(filename):
#     """
#     Returns a Template object comprising the contents of the 
#     file specified by filename.
#     """
    
#     with open(filename, 'r', encoding='utf-8') as template_file:
#         template_file_content = template_file.read()
#     return Template(template_file_content)

def send_email_smtp():
    # set up the SMTP server
    s = smtplib.SMTP(host=HOST, port=PORT)
    s.starttls()
    s.login(SMTP_USERNAME, SMTP_PASSWORD)

    msg = MIMEMultipart()       # create a message
    message = "hello world 2"

    # Prints out the message body for our sake
    print(message)
    
    to_addr = "mr7172@nyu.edu"

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
    return send_email_smtp()
    # return send_mail("mayankr99+aws@gmail.com", "mr7172@nyu.edu", "hello world!")
