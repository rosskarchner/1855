#!/bin/sh
sam build
sam package --s3-bucket ross-sam --output-template-file deploy.yml
sam deploy --template-file deploy.yml  --stack-name sam-indieauth --capabilities CAPABILITY_IAM
