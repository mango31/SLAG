#!/bin/bash

# Set variables
ENVIRONMENT="production"
AWS_REGION="us-west-2"
AWS_ACCOUNT_ID="047719630676"
ECR_REPO="vmini-engine-worker-production"
CLUSTER_NAME="vMini-engine-production"
SERVICE_NAME="vmini-engine-worker-service"
IAM_ROLE="vmini-engine-role"

# Ensure CloudWatch Logs permissions
echo "Updating IAM role permissions..."
POLICY_ARN=$(aws iam create-policy \
    --policy-name vmini-engine-worker-logs \
    --policy-document file://deploy/cloudwatch-policy.json \
    --query 'Policy.Arn' \
    --output text 2>/dev/null || \
    aws iam get-policy \
        --policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/vmini-engine-worker-logs \
        --query 'Policy.Arn' \
        --output text)

# Attach policy if not already attached
aws iam attach-role-policy \
    --role-name $IAM_ROLE \
    --policy-arn $POLICY_ARN || true

# Ensure S3 permissions
echo "Updating IAM role S3 permissions..."
S3_POLICY_ARN=$(aws iam create-policy \
    --policy-name vmini-engine-worker-s3 \
    --policy-document file://deploy/s3-policy.json \
    --query 'Policy.Arn' \
    --output text 2>/dev/null || \
    aws iam get-policy \
        --policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/vmini-engine-worker-s3 \
        --query 'Policy.Arn' \
        --output text)

# Attach policy if not already attached
aws iam attach-role-policy \
    --role-name $IAM_ROLE \
    --policy-arn $S3_POLICY_ARN || true

# Build and tag Docker image
docker buildx build --platform linux/amd64 --load -t ${ECR_REPO}:latest .

# Login to ECR
aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Tag and push image
docker tag ${ECR_REPO}:latest ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}:latest
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}:latest

# Register task definition
echo "Registering task definition..."
TASK_DEFINITION_ARN=$(aws ecs register-task-definition \
    --cli-input-json file://deploy/task-definition.json \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)

# Check if service exists
SERVICE_STATUS=$(aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --query 'length(services)' \
    --output text 2>/dev/null || echo "0")

if [ "$SERVICE_STATUS" == "0" ]; then
    echo "Creating new ECS service..."
    aws ecs create-service \
        --cluster $CLUSTER_NAME \
        --service-name $SERVICE_NAME \
        --task-definition $TASK_DEFINITION_ARN \
        --desired-count 6 \
        --launch-type FARGATE \
        --enable-execute-command \
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
        --desired-count 6 \
        --force-new-deployment
fi

# Wait for service to be active
echo "Waiting for service to become active..."
aws ecs wait services-stable \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME

# Verify service is running
echo "Verifying service status..."
aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --query 'services[0].{Status:status,DesiredCount:desiredCount,RunningCount:runningCount}'

echo "Deployment complete!" 