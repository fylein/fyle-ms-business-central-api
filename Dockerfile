# Pull python base image
FROM python:3.11-slim

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get -y install libpq-dev gcc && apt-get install git postgresql-client -y --no-install-recommends

# Installing requirements
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install -r /tmp/requirements.txt && pip install flake8

# Copy Project to the container
RUN mkdir -p /fyle-ms-business-central-api
COPY . /fyle-ms-business-central-api/
WORKDIR /fyle-ms-business-central-api

# Do linting checks
RUN flake8 .

#================================================================
# Set default GID if not provided during build
#================================================================
ARG SERVICE_GID=1001

#================================================================
# Setup non-root user and permissions
#================================================================
RUN groupadd -r -g ${SERVICE_GID} ms_business_central_service && \
    useradd -r -g ms_business_central_service ms_business_central_user && \
    chown -R ms_business_central_user:ms_business_central_service /fyle-ms-business-central-api

# Switch to non-root user
USER ms_business_central_user

# Expose development port
EXPOSE 8000

# Run development server
CMD /bin/bash run.sh
