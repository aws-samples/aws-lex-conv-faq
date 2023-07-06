import json
import boto3
import time
from sagemaker.huggingface import get_huggingface_llm_image_uri
from sagemaker.huggingface import HuggingFaceModel

# get image from huggingface
llm_image = get_huggingface_llm_image_uri(
  "huggingface",
  version="0.8.2"
)

assume_role_policy_document = json.dumps({
    "Version": "2012-10-17",
    "Statement": [
        {
        "Effect": "Allow",
        "Principal": {
            "Service": [
                "sagemaker.amazonaws.com",
                "ecs.amazonaws.com"
            ]
        },
        "Action": "sts:AssumeRole"
        }
    ]
})

# editable to whatever you want your endpoint and role to be. You can use an existing role or a new one
# IMPORTANT: make sure your lambda endpoint name in lambda_app.py is consisitent if you change it here
SAGEMAKER_IAM_ROLE_NAME = 'Sagemaker-Endpoint-Creation-Role'
SAGEMAKER_ENDPOINT_NAME = "huggingface-pytorch-sagemaker-endpoint"

# Create role and give sagemaker permissions
def get_iam_role(role_name=SAGEMAKER_IAM_ROLE_NAME):
    iam_client = boto3.client('iam')

    try: 
        role = iam_client.get_role(RoleName=role_name)
        role_arn = role['Role']['Arn']
        print(f"Role {role_arn} found!")
        return role_arn
    
    except:
        role_arn = iam_client.create_role(
            RoleName=SAGEMAKER_IAM_ROLE_NAME,
            AssumeRolePolicyDocument=assume_role_policy_document
            )['Role']['Arn']

        time.sleep(10) # give the policy some time to properly create

        response = iam_client.attach_role_policy(
            PolicyArn='arn:aws:iam::aws:policy/AmazonSageMakerFullAccess',
            RoleName=SAGEMAKER_IAM_ROLE_NAME,
        )
        print(f"Creating {role_arn}")
        time.sleep(20) # give iam time to let the role create
        return role_arn


# Define Model and Endpoint configuration parameter

health_check_timeout = 300
trust_remote_code = True

# Create sagemaker endpoint, default values are flan t5 xxl in a g5.8xl instance
def create_endpoint_from_HF_image(hf_model_id, instance_type="ml.g5.8xlarge", endpoint_name=SAGEMAKER_ENDPOINT_NAME, number_of_gpu=1):
    sagemaker_client = boto3.client('sagemaker')

    try: # check if endpoint already existst
        sagemaker_client.describe_endpoint(EndpointName=SAGEMAKER_ENDPOINT_NAME)
        print(f"Endpoint with name {SAGEMAKER_ENDPOINT_NAME} found!")
        return
    
    except:
        print(f"Creating endpoint with model{hf_model_id} on {instance_type}...")

        # create HuggingFaceModel with the image uri
        llm_model = HuggingFaceModel(
            role=get_iam_role(),
            image_uri=llm_image,
            env={
                'HF_MODEL_ID': hf_model_id,
                'SM_NUM_GPUS': json.dumps(number_of_gpu),
                'HF_MODEL_TRUST_REMOTE_CODE': json.dumps(trust_remote_code)
            }
        )

        # Deploy model to an endpoint
        # https://sagemaker.readthedocs.io/en/stable/api/inference/model.html#sagemaker.model.Model.deploy
        llm = llm_model.deploy(
            endpoint_name=endpoint_name,
            initial_instance_count=1,
            instance_type=instance_type,
            # volume_size=400, # If using an instance with local SSD storage, volume_size must be None, e.g. p4 but not p3
            container_startup_health_check_timeout=health_check_timeout  # 10 minutes to be able to load the model
        )

        print(f"\nEndpoint created ({endpoint_name})")
