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

build() {
  echo "---------------------------"
  echo "Building deployment package"
  echo "---------------------------"
  echo ""

  if [ ! -d deploy ]; then
      mkdir deploy
  fi

  if [ ! -d ${DIST_DIR_NAME} ]; then
      mkdir ${DIST_DIR_NAME}
  fi

  dist_path=${PROJECT_ROOT}/${DIST_DIR_NAME}


  echo "Cleaning up dist and deploy directory ..."
  rm -rf ${dist_path}/*
  rm -rf ${PROJECT_ROOT}/${DEPLOY_DIR_NAME}/*

  echo "Copying project files ..."
  cp -rf ${PROJECT_ROOT}/src/* ${dist_path}

  echo "Adding pip libs ..."
  pip install -r requirements.txt -t ${dist_path}/

  echo "Adding google directory ..."
  mkdir ${dist_path}/google
  touch ${dist_path}/google/__init__.py

  cd ${dist_path}
  zip -r ${PROJECT_ROOT}/${DEPLOY_DIR_NAME}/${LAMBDA_CODE_FILE} *

  ls -la ${PROJECT_ROOT}/${DEPLOY_DIR_NAME}/
  echo ${PROJECT_ROOT}/${DEPLOY_DIR_NAME}/${LAMBDA_CODE_FILE}
  cd ${PROJECT_ROOT}
}

build
