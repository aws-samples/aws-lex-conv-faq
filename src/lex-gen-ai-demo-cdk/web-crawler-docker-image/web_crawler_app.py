import boto3
import requests
import html2text
from typing import List
import re
import logging
import json
import traceback

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def find_http_urls_in_parentheses(s: str, prefix: str = None):
    pattern = r'\((https?://[^)]+)\)'
    urls = re.findall(pattern, s)

    matched = []
    if prefix is not None:
        for url in urls:
            if str(url).startswith(prefix):
                matched.append(url)
    else:
        matched = urls

    return list(set(matched))  # remove duplicates by converting to set, then convert back to list



class EZWebLoader:

    def __init__(self, default_header: str = None):
        self._html_to_text_parser = html2text
        if default_header is None:
            self._default_header =  {"User-agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36"}
        else:
            self._default_header = default_header

    def load_data(self,
                  urls: List[str],
                  num_levels: int = 0,
                  level_prefix: str = None,
                  headers: str = None) -> List[str]:

        logging.info(f"Number of urls: {len(urls)}.")

        if headers is None:
            headers = self._default_header

        documents = []
        visited = {}
        for url in urls:
            q = [url]
            depth = num_levels
            for page in q:
                if page not in visited:     #prevent cycles by checking to see if we already crawled a link
                    logging.info(f"Crawling {page}")
                    visited[page] = True   #add entry to visited to prevent re-crawling pages
                    response = requests.get(page, headers=headers).text
                    response = self._html_to_text_parser.html2text(response)  #reduce html to text
                    documents.append(response)
                    if depth > 0:
                        #crawl linked pages
                        ingest_urls = find_http_urls_in_parentheses(response, level_prefix)
                        logging.info(f"Found {len(ingest_urls)} pages to crawl.")
                        q.extend(ingest_urls)
                        depth -= 1  #reduce the depth counter so we go only num_levels deep in our crawl
                else:
                    logging.info(f"Skipping {page} as it has already been crawled")
        logging.info(f"Number of documents: {len(documents)}.")
        return documents

ACCOUNT_ID = boto3.client('sts').get_caller_identity().get('Account')
S3_BUCKET = "lexgenaistack-source-materials-bucket-" + ACCOUNT_ID
FILE_NAME = 'web-crawl-results.txt'


def handler(event, context):
    url = "http://www.zappos.com/general-questions"
    depth = 1
    level_prefix = "https://www.zappos.com/"

    if event is not None:
        if "url" in event:
            url = event["url"]
        if "depth" in event:
            depth = int(event["depth"])
        if "level_prefix" in event:
            level_prefix = event["level_prefix"]

    # crawl the website
    try:
        logger.info(f"Crawling {url} to depth of {depth}...")
        loader = EZWebLoader()
        documents = loader.load_data([url], depth, level_prefix)
        doc_string = json.dumps(documents, indent=1)
        logger.info(f"Crawling {url} to depth of {depth} succeeded")
    except Exception as e:
        # If there's an error, print the error message
        logging.error(f"An error occurred during the crawl of {url}.")
        exception_traceback = traceback.format_exc()
        logger.error(exception_traceback)
        return {
            "status": 500,
            "message": exception_traceback
        }
    # save the results for indexing
    try:
        # Use the S3 client to write the string to S3
        s3 = boto3.client('s3')
        s3.put_object(Body=doc_string, Bucket=S3_BUCKET, Key=FILE_NAME)
        success_msg = f'Successfully put {FILE_NAME} to {S3_BUCKET}'
        logging.info(success_msg)
        return {
            "status": 200,
            "message": success_msg
        }
    except Exception as e:
        # If there's an error, print the error message
        exception_traceback = traceback.format_exc()
        logger.error(exception_traceback)
        return {
            "status": 500,
            "message": exception_traceback
        }
