#!/usr/bin/env bash

#running clamAV process in a background
echo "Starting clamd..."
clamd
echo "Clamd started"

echo "Installing awscli using pip"
pip3 install awscli --upgrade
aws --version

echo "Creating SNS virus notification topic"
AWS_ACCESS_KEY_ID=${AWS_SNS_ACCESS_KEY_ID} \
AWS_SECRET_ACCESS_KEY=${AWS_SNS_SECRET_ACCESS_KEY} \
aws --region=${AWS_SNS_REGION} --endpoint-url=${AWS_SNS_ENDPOINT_URL} sns create-topic --name ${VIRUS_NOTIFICATION_TOPIC_ARN##*:}

make test-ci
