from aws_cdk import (
    Duration, App, Stack, CfnResource,
    aws_lex as lex,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_s3_deployment as s3deploy,
    aws_iam as iam,
    aws_lambda as lambda_
)

from constructs import Construct

class LexGenAIDemoFilesStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Iam role for bot to invoke lambda
        lex_cfn_role = iam.Role(self, "CfnLexGenAIDemoRole",
            assumed_by=iam.ServicePrincipal("lexv2.amazonaws.com")
        )
        lex_cfn_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AWSLambdaExecute")) 

        # Iam role for lambda to invoke sagemaker
        lambda_cfn_role = iam.Role(self, "CfnLambdaGenAIDemoRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com")
        )
        lambda_cfn_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess"))
        lambda_cfn_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess")) 

        # will append account id to this string to avoid in region collisions
        source_bucket_name = "lexgenaistack-source-materials-bucket-"
        index_bucket_name = "lexgenaistack-created-index-bucket-"

        # S3 Buckets for materials to index and for the resulting indexes
        source_bucket = s3.Bucket(self, "SourceMatBucketID-CFN", 
                                  bucket_name=source_bucket_name+lex_cfn_role.principal_account,
                                  block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
                                  encryption=s3.BucketEncryption.S3_MANAGED,
                                  enforce_ssl=True,
                                  versioned=True)
        
        index_bucket = s3.Bucket(self, "IndexBucket-CFN", 
                                 bucket_name=index_bucket_name+lex_cfn_role.principal_account,
                                 block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
                                 encryption=s3.BucketEncryption.S3_MANAGED,
                                 enforce_ssl=True,
                                 versioned=True)

        # create lambda image for on demand index creation
        read_source_and_build_index_function = lambda_.DockerImageFunction(self, "read-source-and-build-index-function-CFN", function_name="read-source-and-build-index-fn",
            code=lambda_.DockerImageCode.from_image_asset("index-creation-docker-image"),
            role=lambda_cfn_role,
            memory_size=10240,
            timeout=Duration.minutes(5)
        )
        source_bucket.add_event_notification(s3.EventType.OBJECT_CREATED, s3n.LambdaDestination(read_source_and_build_index_function))

        # create image of lex-gen-ai-demo-docker-image, push to ECR and into a lambda function
        runtime_function = lambda_.DockerImageFunction(self, "CFN-runtime-fn", function_name="lex-codehook-fn",
            code=lambda_.DockerImageCode.from_image_asset("lex-gen-ai-demo-docker-image"),
            role=lambda_cfn_role,
            memory_size=10240,
            timeout=Duration.minutes(5)
        )
        runtime_function.grant_invoke(iam.ServicePrincipal("lexv2.amazonaws.com"))

        ### BOT SETUP

        # alias settings, where we define the lambda function with the ECR container with our LLM dialog code (defined in the lex-gen-ai-demo-docker-image directory)
        # test bot alias for demo, create a dedicated alias for serving traffic
        bot_alias_settings = lex.CfnBot.TestBotAliasSettingsProperty(
                                        bot_alias_locale_settings=[lex.CfnBot.BotAliasLocaleSettingsItemProperty(
                                            bot_alias_locale_setting=lex.CfnBot.BotAliasLocaleSettingsProperty(
                                                enabled=True,
                                                code_hook_specification=lex.CfnBot.CodeHookSpecificationProperty(
                                                    lambda_code_hook=lex.CfnBot.LambdaCodeHookProperty(
                                                        code_hook_interface_version="1.0",
                                                        lambda_arn=runtime_function.function_arn
                                                    )
                                                )
                                            ),
                                            locale_id="en_US"
                                        )])
        
        # lambda itself is tied to alias but codehook settings are intent specific
        initial_response_codehook_settings = lex.CfnBot.InitialResponseSettingProperty(
                                        code_hook=lex.CfnBot.DialogCodeHookInvocationSettingProperty(
                                            enable_code_hook_invocation=True,
                                            is_active=True,
                                            post_code_hook_specification=lex.CfnBot.PostDialogCodeHookInvocationSpecificationProperty()
                                        )
                                    )
        
        # placeholder intent to be missed for this demo
        placeholder_intent = lex.CfnBot.IntentProperty(
                                    name="placeHolderIntent",
                                    initial_response_setting=initial_response_codehook_settings,
                                    sample_utterances=[lex.CfnBot.SampleUtteranceProperty(
                                                            utterance="utterance"
                                                        )]
                                )
        
        fallback_intent = lex.CfnBot.IntentProperty(
                                    name="FallbackIntent",
                                    parent_intent_signature="AMAZON.FallbackIntent",
                                    initial_response_setting=initial_response_codehook_settings,
                                    fulfillment_code_hook=lex.CfnBot.FulfillmentCodeHookSettingProperty(
                                        enabled=True,
                                        is_active=True,
                                        post_fulfillment_status_specification=lex.CfnBot.PostFulfillmentStatusSpecificationProperty()
                                    )
                                )

        # Create actual Lex Bot
        cfn_bot = lex.CfnBot(self, "LexGenAIDemoCfnBot",
            data_privacy={"ChildDirected":"false"},
            idle_session_ttl_in_seconds=300,
            name="LexGenAIDemoBotCfn",
            role_arn=lex_cfn_role.role_arn,
            bot_locales=[lex.CfnBot.BotLocaleProperty(
                            locale_id="en_US",
                            nlu_confidence_threshold=0.4,
                            intents=[placeholder_intent, fallback_intent])
                        ],
            test_bot_alias_settings = bot_alias_settings,
            auto_build_bot_locales=True
        )

        
