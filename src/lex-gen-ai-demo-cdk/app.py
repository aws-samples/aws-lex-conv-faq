
import aws_cdk as cdk

from lex_gen_ai_demo_cdk_files.lex_gen_ai_demo_cdk_files_stack import LexGenAIDemoFilesStack
from endpoint_handler import create_endpoint_from_HF_image

# create_endpoint_from_HF_image(hf_model_id, instance_type="ml.g5.8xlarge", endpoint_name=SAGEMAKER_ENDPOINT_NAME, number_of_gpu=1)
# You can run with no arguments to get default values of google/flan-t5-xxl on ml.g5.8xlarge, or pass in your own arguments
create_endpoint_from_HF_image(hf_model_id="tiiuae/falcon-7b-instruct")

app = cdk.App()
filestack = LexGenAIDemoFilesStack(app, "LexGenAIDemoFilesStack")

app.synth()
