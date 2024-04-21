# Container image that runs your code
FROM public.ecr.aws/bitnami/python:3.11

# Copies your code file from your action repository to the filesystem path `/` of the container
WORKDIR /app
COPY requirements.txt .
RUN python3 -m pip install -r /app/requirements.txt
COPY action.py .
# Code file to execute when the docker container starts up (`action.py`)
CMD ["python3","-u","/app/action.py"]
