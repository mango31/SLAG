#!/bin/bash

# Set variables
ENVIRONMENT="production"
AWS_REGION="us-west-2"
AWS_ACCOUNT_ID="047719630676"
CLUSTER_NAME="vMini-engine-production"
SERVICE_NAME="vmini-engine-worker-service"

# Register the task definition
echo "Registering worker task definition..."
TASK_DEFINITION_ARN=$(aws ecs register-task-definition \
    --cli-input-json file://worker-task-definition.json \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)

# Check if service exists
SERVICE_STATUS=$(aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --query 'services[0].status' \
    --output text 2>/dev/null || echo "MISSING")

if [ "$SERVICE_STATUS" == "MISSING" ]; then
    echo "Creating new ECS service..."
    aws ecs create-service \
        --cluster $CLUSTER_NAME \
        --service-name $SERVICE_NAME \
        --task-definition $TASK_DEFINITION_ARN \
        --desired-count 1 \
        --launch-type FARGATE \
        --network-configuration '{
            "awsvpcConfiguration": {
                "subnets": ["subnet-08e2f4a63424670d9", "subnet-07754accd2f3042f7"],
                "securityGroups": ["sg-04515fc78b0af01dd", "sg-0b0664e5fa92bbb6d"],
                "assignPublicIp": "ENABLED"
            }
        }'
else
    echo "Updating existing ECS service..."
    aws ecs update-service \
        --cluster $CLUSTER_NAME \
        --service $SERVICE_NAME \
        --task-definition $TASK_DEFINITION_ARN \
        --network-configuration '{
            "awsvpcConfiguration": {
                "subnets": ["subnet-08e2f4a63424670d9", "subnet-07754accd2f3042f7"],
                "securityGroups": ["sg-04515fc78b0af01dd", "sg-0b0664e5fa92bbb6d"],
                "assignPublicIp": "ENABLED"
            }
        }' \
        --force-new-deployment
fi

# Monitor deployment
echo "Monitoring deployment..."
aws ecs wait services-stable \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME

if [ $? -eq 0 ]; then
    echo "Worker service deployment complete!"
    
    # Show running tasks
    TASKS=$(aws ecs list-tasks \
        --cluster $CLUSTER_NAME \
        --service-name $SERVICE_NAME \
        --query 'taskArns[]' \
        --output text)
    
    if [ ! -z "$TASKS" ]; then
        echo "Checking task status..."
        aws ecs describe-tasks \
            --cluster $CLUSTER_NAME \
            --tasks $TASKS \
            --query 'tasks[].{Status:lastStatus,Health:healthStatus,Reason:stoppedReason}'
    fi
else
    echo "Deployment failed. Checking service events..."
    aws ecs describe-services \
        --cluster $CLUSTER_NAME \
        --services $SERVICE_NAME \
        --query 'services[0].events[0:5]'
fi 