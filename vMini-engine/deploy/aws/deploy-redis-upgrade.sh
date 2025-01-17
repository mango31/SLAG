#!/bin/bash

# Set variables
ENVIRONMENT="production"
AWS_REGION="us-west-2"
EXISTING_SG="sg-0b0664e5fa92bbb6d"  # Your Redis security group
STACK_NAME="vMini-engine-redis-upgrade"

# Check if stack exists and delete if in ROLLBACK_COMPLETE
STACK_STATUS=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query 'Stacks[0].StackStatus' \
    --output text 2>/dev/null || echo "DOES_NOT_EXIST")

if [ "$STACK_STATUS" = "ROLLBACK_COMPLETE" ]; then
    echo "Cleaning up failed stack..."
    aws cloudformation delete-stack --stack-name $STACK_NAME
    aws cloudformation wait stack-delete-complete --stack-name $STACK_NAME
fi

# Get existing subnet group name
SUBNET_GROUP="vmini-engine-redis-subnet"

if [ -z "$SUBNET_GROUP" ]; then
    echo "Error: No subnet group found"
    exit 1
fi

echo "Using subnet group: $SUBNET_GROUP"

# Deploy Redis Upgrade Stack
echo "Deploying Redis upgrade stack..."
aws cloudformation create-stack \
    --stack-name $STACK_NAME \
    --template-body file://redis-upgrade.yml \
    --parameters \
        ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
        ParameterKey=ExistingRedisSecurityGroup,ParameterValue=$EXISTING_SG \
        ParameterKey=ExistingSubnetGroup,ParameterValue=$SUBNET_GROUP \
    --capabilities CAPABILITY_IAM

echo "Waiting for Redis upgrade stack to complete..."
aws cloudformation wait stack-create-complete --stack-name $STACK_NAME

if [ $? -eq 0 ]; then
    # Get new Redis endpoint
    NEW_REDIS_ENDPOINT=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --query 'Stacks[0].Outputs[?OutputKey==`NewRedisEndpoint`].OutputValue' \
        --output text)
    
    echo "Stack creation successful!"
    echo "New Redis endpoint: $NEW_REDIS_ENDPOINT"
    echo "Please update your environment variables with the new endpoint"
else
    echo "Stack creation failed. Checking events:"
    aws cloudformation describe-stack-events \
        --stack-name $STACK_NAME \
        --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`].[LogicalResourceId,ResourceStatusReason]' \
        --output text
fi 