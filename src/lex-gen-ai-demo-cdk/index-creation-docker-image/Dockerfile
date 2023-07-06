FROM public.ecr.aws/lambda/python:3.8

COPY index_creation_requirements.txt  .
RUN  pip3 install -r index_creation_requirements.txt --target "${LAMBDA_TASK_ROOT}"
 
# Copy function code
COPY *.py ${LAMBDA_TASK_ROOT}
 
# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "index_creation_app.handler" ]

# Set cache to a location lambda can write to
ENV TRANSFORMERS_CACHE="/tmp/TRANSFORMERS_CACHE"

