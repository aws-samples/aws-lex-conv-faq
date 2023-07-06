from aws_cdk import (
    Duration, Stack,
    aws_lambda as lambda_,
    aws_s3 as s3,
    aws_iam as iam
)

from constructs import Construct

class LambdaStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        # Iam role for lambda to invoke sagemaker
        web_crawl_lambda_cfn_role = iam.Role(self, "Cfn-gen-ai-demo-web-crawler",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com")
        )
        web_crawl_lambda_cfn_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"))
        web_crawl_lambda_cfn_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                resources=["*"]
            )
        )
        # Lambda function
        lambda_function= lambda_.DockerImageFunction(self, "web-crawler-docker-image-CFN",
                                    function_name="WebCrawlerLambda",
                                    code=lambda_.DockerImageCode.from_image_asset("web-crawler-docker-image"),
                                    role=web_crawl_lambda_cfn_role,
                                    memory_size=1024,
                                    timeout=Duration.minutes(5)
                                    )
