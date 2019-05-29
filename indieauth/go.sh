#!/bin/sh
isort -rc --atomic auth
black -t py36 .
sam build
sam package --s3-bucket ross-sam --output-template-file deploy.yml
sam deploy --template-file deploy.yml  --stack-name sam-indieauth --capabilities CAPABILITY_IAM\
    --parameter-overrides HostedZoneName=karchner.com  CognitoSubdomain=auth \
    CertificateArn="arn:aws:acm:us-east-1:797438674243:certificate/22e6a31c-bb50-46ec-ab62-1dc56bece5dc"
