# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# The Google Cloud Platform Python runtime is based on Debian Jessie
# You can read more about the runtime at:
#   https://github.com/GoogleCloudPlatform/python-runtime
FROM gcr.io/google_appengine/python

# Create a virtualenv for dependencies. This isolates these packages from
# system-level packages.
RUN virtualenv -p python3.7 /env

# Setting these environment variables are the same as running
# source /env/bin/activate.
ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH

ADD . /chat-app/

WORKDIR /chat-app
RUN pip install -r requirements.txt

# Need to regenerate *_pb2.py and *_grpc.py, because GCP runs a different 
# version than local, for the following python packages:
#
# Local:
# - python: 3.12
# - protobuf: 5.28.1
# - grpcio & grpcio-tools: 1.59.0
#
# Cloud:
# - python: 3.7
# - protobuf: 3.19.6
# - grpcio & grpcio-tools: 1.48.2
RUN python -m grpc_tools.protoc \
    --include_imports \
    --include_source_info \
    --proto_path=proto/ \
    --descriptor_set_out=proto/api_descriptor.pb \
    --python_out=proto/generated_pb2 \
    --grpc_python_out=proto/generated_pb2 \
    proto/chat_service.proto

ENTRYPOINT ["python", "/chat-app/chat_server.py"]