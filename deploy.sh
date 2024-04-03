#!/bin/bash
# Copyright 2024 ASL19 Organization
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Project config
PROJECT_ROOT=`pwd`
DIST_DIR_NAME="dist"
DEPLOY_DIR_NAME="deploy"
LAMBDA_CODE_FILE=lambda.zip

# AWS Config
LAMBDA_HANDLER=outlinebot.bot_handler
LAMBDA_FUNCTION_NAME=${AWS_LAMBDA_FUNCTION_NAME}
REGION=${AWS_LAMBDA_REGION_NAME}
AWS_ACCOUNT=${AWS_ACCOUNT}
AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
LAMBDA_DESCRIPTION="BeePass Distribution Bot"
##
LAMBDA_ROLE=${LAMBDA_ROLE}
LAMBDA_TIMEOUT=180
LAMBDA_MEMORY=256
## Python version
RUNTIME=python3.8
## TAGS
TAG_ACCOUNT=${TAG_ACCOUNT}
TAG_PROJECT=${TAG_PROJECT}
TAG_PURPOSE=${TAG_PURPOSE}

update_env_variables() {
  # update function
  echo "----------------------------"
  echo "Update Environment Variables"
  echo "----------------------------"
  echo "Lambda role:"
  echo ${LAMBDA_ROLE}
  AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
  AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
  aws lambda update-function-configuration \
    --region ${REGION} \
    --function-name ${LAMBDA_FUNCTION_NAME} \
    --handler ${LAMBDA_HANDLER} \
    --description "${LAMBDA_DESCRIPTION}" \
    --role arn:aws:iam::${AWS_ACCOUNT}:role/${LAMBDA_ROLE} \
    --runtime ${RUNTIME} \
    --timeout ${LAMBDA_TIMEOUT} \
    --memory-size ${LAMBDA_MEMORY} \
    --environment '{"Variables": {"DEBUG": "False"}}'
}


update_lambda() {
  # update function
  echo "-----------------------------"
  echo "Update Lambda function on AWS"
  echo "-----------------------------"
  echo ""
  AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
  AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
  aws lambda update-function-code \
    --region ${REGION} \
    --function-name ${LAMBDA_FUNCTION_NAME} \
    --zip-file fileb://${PROJECT_ROOT}/${DEPLOY_DIR_NAME}/${LAMBDA_CODE_FILE}
}

publish_lambda() {
  # update function
  echo "-----------------------------"
  echo "Publish Lambda function on AWS"
  echo "-----------------------------"
  echo ""
  local __resultvar=$1
  AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
  AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
  local version=$(aws lambda publish-version \
    --region ${REGION} \
    --function-name ${LAMBDA_FUNCTION_NAME} \
    --query 'Version')
  if [[ "$__resultvar" ]]; then
      eval $__resultvar=$version
  else
      echo $version
  fi
}

update_alias() {
  # update function
  echo "-------------------------------------"
  echo "Update Lambda function's Alias on AWS"
  echo "-------------------------------------"
  echo ""
  local __new_version=$1
  AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
  AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
  if [[ "$__new_version" ]]; then
  aws lambda update-alias \
    --region ${REGION} \
    --function-name ${LAMBDA_FUNCTION_NAME} \
    --name "stable" \
    --function-version $__new_version
  else
      echo "The version number is missing"
  fi
}

create_lambda() {
  # create new function
  echo "-----------------------------"
  echo "Create Lambda function on AWS"
  echo "-----------------------------"
  echo ""
   AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
   AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
   aws lambda create-function \
    --region ${REGION} \
    --function-name ${LAMBDA_FUNCTION_NAME} \
    --description "${LAMBDA_DESCRIPTION}" \
    --zip-file fileb://${PROJECT_ROOT}/${DEPLOY_DIR_NAME}/${LAMBDA_CODE_FILE} \
    --role arn:aws:iam::${AWS_ACCOUNT}:role/${LAMBDA_ROLE} \
    --handler ${LAMBDA_HANDLER} \
    --runtime ${RUNTIME} \
    --timeout ${LAMBDA_TIMEOUT} \
    --memory-size ${LAMBDA_MEMORY} \
    --tags Account=${TAG_ACCOUNT},Project=${TAG_PROJECT},Purpose=${TAG_PURPOSE}
}

deploy() {
  echo "-----------------------"
  echo "Deploying to AWS Lambda"
  echo "-----------------------"
  echo ""

  # if function already exists
  if aws lambda get-function --region ${REGION} --function-name ${LAMBDA_FUNCTION_NAME} > /dev/null; then
    update_lambda
    sleep 15
    # update_env_variables
    publish_lambda new_version
    echo $new_version
    sleep 5
    update_alias $new_version
  else
    create_lambda
    sleep 15
    # update_env_variables
    publish_lambda new_version
    echo $new_version
    # Todo: Create Alias with the new version

  fi
}

deploy
