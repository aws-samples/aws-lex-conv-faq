FROM public.ecr.aws/lambda/python:3.8

COPY runtime_lambda_requirements.txt  .
RUN  pip3 install -r runtime_lambda_requirements.txt --target "${LAMBDA_TASK_ROOT}"
 
# Copy function code
COPY *.py ${LAMBDA_TASK_ROOT}
 
# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "runtime_lambda_app.handler" ]

# Set cache to a location lambda can write to
ENV TRANSFORMERS_CACHE="/tmp/TRANSFORMERS_CACHE"

