#!/bin/sh
set -e
cfn-lint -t template.yaml
black -t py36 .
isort -rc --atomic micropub
sam build
sam package --s3-bucket ross-sam --output-template-file deploy.yml
sam deploy --template-file deploy.yml  --stack-name blog --capabilities CAPABILITY_IAM\
 --parameter-overrides DomainName=ross.karchner.com  BlogName="Under Construction 👷🚧👷️" \
    BlogDescription="Notes on code and cloud"\
    AuthEndpointURL="https://indieauth.com/auth"\
    TokenEndpointURL="https://tokens.indieauth.com/token"\
    RelMeLinks="https://github.com/rosskarchner,https://micro.blog/rossk,https://twitter.com/rossk"\
    CertificateArn="arn:aws:acm:us-east-1:797438674243:certificate/22e6a31c-bb50-46ec-ab62-1dc56bece5dc"\
    DomainName=ross.karchner.com TimeZone="US/Eastern"
