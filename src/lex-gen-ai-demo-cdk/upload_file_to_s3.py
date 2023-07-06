import sys
import boto3
from botocore.exceptions import ClientError
import logging

ACCOUNT_ID = boto3.client('sts').get_caller_identity().get('Account')
S3_BUCKET = "lexgenaistack-source-materials-bucket-"+ACCOUNT_ID
s3_client = boto3.client("s3")

def main():
    if len(sys.argv) == 1:
        print(f"[ERROR] You must specify file to upload")
    elif len(sys.argv) == 2:
        filepath = sys.argv[1]
        upload(filepath)
    elif len(sys.argv) == 3:
        filepath = sys.argv[2]
        upload(filepath)
    else:
        print("[ERROR] Too many arguments, only include /path/to/your/file")


def upload(filepath):
    if filepath[-4:].lower() == '.txt' or filepath[-4:].lower() == '.pdf':
        print(f"Uploading file at {filepath}")
        try:
            upload_name = filepath.split("/")[-1].replace(" ","").replace("/","")
            s3_client.upload_file(filepath, S3_BUCKET, upload_name) 
            print(f"Successfully uploaded file at {filepath}, creating index...")
        except ClientError as e:
            logging.error(e)
    else:
        print("[ERROR] File must be txt or PDF")


if __name__ == "__main__":
    main()