import boto3
import argparse
import json


def invoke_lambda(url=None, depth="1", level_prefix=None):
    client = boto3.client('lambda')

    # Prepare the payload
    payload = {}
    if url is not None:
        payload["url"] = url
    if depth is not None:
        payload["depth"] = depth
    if level_prefix is not None:
        payload["level_prefix"] = level_prefix

    try:
        response = client.invoke(
            FunctionName='WebCrawlerLambda',
            InvocationType='RequestResponse',
            LogType='Tail',
            # The payload must be a JSON-formatted string
            Payload=json.dumps(payload)
        )

        # The response from Lambda will be a JSON string, so you need to parse it
        result = response['Payload'].read().decode('utf-8')

        print("Response: " + result)

    except Exception as e:
        print(e)


# Parse command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--url', type=str, help='The URL to process.', required=False, default=None)
parser.add_argument('--depth', type=int, help='The depth of the crawl.', required=False, default="1")
parser.add_argument('--level_prefix', type=str, help='The prefix that any links must contain to crawl.', required=False, default=None)
args = parser.parse_args()

invoke_lambda(args.url, args.depth, args.level_prefix)
