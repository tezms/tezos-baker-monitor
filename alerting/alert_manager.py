import requests
import os
import boto3
import datetime

# Optionally send alerts to AWS CloudWatch
IDENTIFIER = os.getenv('IDENTIFIER', 'tezos-monitor')
SEND_TO_CLOUDWATCH = os.getenv('SEND_TO_CLOUDWATCH', 'false').lower() == 'true'
CLOUDWATCH_LOG_GROUP = os.getenv('CLOUDWATCH_LOG_GROUP', 'TezosBakerMonitorAlerts')
CLOUDWATCH_STREAM_NAME = os.getenv('CLOUDWATCH_STREAM_NAME', IDENTIFIER)

# Optionally send alerts to Telegram
SEND_TO_TELEGRAM = os.getenv('SEND_TO_TELEGRAM', 'false').lower() == 'true'
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
REGION = os.getenv('AWS_REGION', 'eu-west-1')

def send_message_to_cloudwatch(message):
    """
    Send alert message to AWS CloudWatch log group.
    Requires AWS credentials to be configured.
    """
    
    client = boto3.client('logs', region_name=REGION)
    timestamp = int(datetime.datetime.now().timestamp() * 1000)
    # Ensure log group exists
    try:
        client.create_log_group(logGroupName=CLOUDWATCH_LOG_GROUP)
    except client.exceptions.ResourceAlreadyExistsException:
        pass
    # Ensure log stream exists
    log_stream_name = CLOUDWATCH_STREAM_NAME
    try:
        client.create_log_stream(logGroupName=CLOUDWATCH_LOG_GROUP, logStreamName=log_stream_name)
    except client.exceptions.ResourceAlreadyExistsException:
        pass
    # Get the next sequence token
    response = client.describe_log_streams(logGroupName=CLOUDWATCH_LOG_GROUP, logStreamNamePrefix=log_stream_name)
    log_streams = response.get('logStreams', [])
    sequence_token = None
    if log_streams and 'uploadSequenceToken' in log_streams[0]:
        sequence_token = log_streams[0]['uploadSequenceToken']
    # Put log event
    log_event = {
        'logGroupName': CLOUDWATCH_LOG_GROUP,
        'logStreamName': log_stream_name,
        'logEvents': [
            {
                'timestamp': timestamp,
                'message': message
            }
        ]
    }
    if sequence_token:
        log_event['sequenceToken'] = sequence_token
    client.put_log_events(**log_event)
    print(f"CloudWatch alert sent: {message}")

def send_message_to_telegram(message):
    """
    Send alert message to a Telegram chat using a bot.
    Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to be set.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram bot token or chat ID not set. Cannot send Telegram alert.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=data)
        if response.status_code != 200:
            print(f"Failed to send Telegram alert: {response.text}")
        else:
            print(f"Telegram alert sent: {message}")
    except Exception as e:
        print(f"Exception sending Telegram alert: {e}")
    

def send_alert(message):
    full_message = f"[{IDENTIFIER}]: ALERT - {message}"
    print(full_message)
    if SEND_TO_CLOUDWATCH:
        send_message_to_cloudwatch(full_message)
    if SEND_TO_TELEGRAM:
        send_message_to_telegram(full_message)

def send_log(message):
    full_message = f"[{IDENTIFIER}]: Log - {message}"
    print(full_message)
    if SEND_TO_CLOUDWATCH:
        send_message_to_cloudwatch(full_message)
    