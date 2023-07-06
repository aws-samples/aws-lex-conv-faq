FROM public.ecr.aws/lambda/python:3.8

COPY web_crawler_requirements.txt  .
RUN  pip3 install -r web_crawler_requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy function code
COPY *.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "web_crawler_app.handler" ]

