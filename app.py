#!/usr/bin/env python3
import os
import aws_cdk as cdk
from network_stack import NetworkStack
from server_stack import ServerStack

app = cdk.App()

# Create the network stack first
network_stack = NetworkStack(
    app,
    "NetworkStack",
    description="Network infrastructure with VPC, subnets across 2 AZs"
)

# Create the server stack, passing the VPC from network stack
server_stack = ServerStack(
    app,
    "ServerStack",
    vpc=network_stack.vpc,
    description="Web servers and RDS MySQL database"
)

# Server stack depends on network stack
server_stack.add_dependency(network_stack)

app.synth()