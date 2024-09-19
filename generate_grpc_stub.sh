#!/bin/bash

python3 -m grpc_tools.protoc \
    --include_imports \
    --include_source_info \
    --proto_path=proto/ \
    --descriptor_set_out=proto/api_descriptor.pb \
    --python_out=proto/generated_pb2 \
    --grpc_python_out=proto/generated_pb2 \
    proto/chat_service.proto