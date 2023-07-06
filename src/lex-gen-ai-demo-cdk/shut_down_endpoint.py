import boto3
from botocore.exceptions import ClientError

from endpoint_handler import SAGEMAKER_ENDPOINT_NAME


sagemaker_client = boto3.client('sagemaker')


try:
    # verify endpoint exists
    endpoint = sagemaker_client.describe_endpoint(EndpointName=SAGEMAKER_ENDPOINT_NAME)
    print(f"Endpoint {endpoint['EndpointName']} found, shutting down")

    try: # delete both endpoint and configuration
        sagemaker_client.delete_endpoint(
            EndpointName=SAGEMAKER_ENDPOINT_NAME
        )
        sagemaker_client.delete_endpoint_config(
            EndpointConfigName=SAGEMAKER_ENDPOINT_NAME
        )
        print(f"Endpoint {SAGEMAKER_ENDPOINT_NAME} shut down")
    except ClientError as e:
        print(e)
except:
    print(f"Endpoint {SAGEMAKER_ENDPOINT_NAME} does not exist in account {boto3.client('sts').get_caller_identity().get('Account')}")