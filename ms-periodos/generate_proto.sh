#!/bin/bash
python -m grpc_tools.protoc -I../proto --python_out=./proto_generated --grpc_python_out=./proto_generated ../proto/periodos.proto
echo 'Stubs generados en proto_generated/'
