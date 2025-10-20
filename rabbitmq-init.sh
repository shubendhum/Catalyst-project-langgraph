#!/bin/bash
# RabbitMQ Initialization Script
# Creates exchanges, queues, and bindings for Catalyst event system

set -e

echo "Waiting for RabbitMQ to be ready..."
sleep 10

# RabbitMQ credentials
RABBITMQ_USER=${RABBITMQ_DEFAULT_USER:-catalyst}
RABBITMQ_PASS=${RABBITMQ_DEFAULT_PASS:-catalyst_queue_2025}
RABBITMQ_VHOST=${RABBITMQ_DEFAULT_VHOST:-catalyst}

# Management API endpoint
API="http://localhost:15672/api"

echo "Creating Catalyst event exchange and queues..."

# Create topic exchange
rabbitmqadmin declare exchange \
  --vhost=$RABBITMQ_VHOST \
  --username=$RABBITMQ_USER \
  --password=$RABBITMQ_PASS \
  name=catalyst.events \
  type=topic \
  durable=true

# Create queues for each agent
for agent in planner architect coder tester reviewer deployer explorer orchestrator; do
  echo "Creating queue: ${agent}-queue"
  
  rabbitmqadmin declare queue \
    --vhost=$RABBITMQ_VHOST \
    --username=$RABBITMQ_USER \
    --password=$RABBITMQ_PASS \
    name=${agent}-queue \
    durable=true \
    arguments='{"x-message-ttl":3600000,"x-max-length":10000}'
done

# Create dead letter queue
rabbitmqadmin declare queue \
  --vhost=$RABBITMQ_VHOST \
  --username=$RABBITMQ_USER \
  --password=$RABBITMQ_PASS \
  name=failed-events \
  durable=true

# Create bindings
echo "Creating bindings..."

# Planner listens to task initiation
rabbitmqadmin declare binding \
  --vhost=$RABBITMQ_VHOST \
  --username=$RABBITMQ_USER \
  --password=$RABBITMQ_PASS \
  source=catalyst.events \
  destination=planner-queue \
  routing_key="catalyst.task.initiated"

# Architect listens to plan created
rabbitmqadmin declare binding \
  --vhost=$RABBITMQ_VHOST \
  --username=$RABBITMQ_USER \
  --password=$RABBITMQ_PASS \
  source=catalyst.events \
  destination=architect-queue \
  routing_key="catalyst.plan.created"

# Coder listens to architecture proposed
rabbitmqadmin declare binding \
  --vhost=$RABBITMQ_VHOST \
  --username=$RABBITMQ_USER \
  --password=$RABBITMQ_PASS \
  source=catalyst.events \
  destination=coder-queue \
  routing_key="catalyst.architecture.proposed"

# Tester listens to code PR opened
rabbitmqadmin declare binding \
  --vhost=$RABBITMQ_VHOST \
  --username=$RABBITMQ_USER \
  --password=$RABBITMQ_PASS \
  source=catalyst.events \
  destination=tester-queue \
  routing_key="catalyst.code.pr.opened"

# Reviewer listens to test results
rabbitmqadmin declare binding \
  --vhost=$RABBITMQ_VHOST \
  --username=$RABBITMQ_USER \
  --password=$RABBITMQ_PASS \
  source=catalyst.events \
  destination=reviewer-queue \
  routing_key="catalyst.test.results"

# Deployer listens to review decision
rabbitmqadmin declare binding \
  --vhost=$RABBITMQ_VHOST \
  --username=$RABBITMQ_USER \
  --password=$RABBITMQ_PASS \
  source=catalyst.events \
  destination=deployer-queue \
  routing_key="catalyst.review.decision"

# Explorer listens to explorer requests
rabbitmqadmin declare binding \
  --vhost=$RABBITMQ_VHOST \
  --username=$RABBITMQ_USER \
  --password=$RABBITMQ_PASS \
  source=catalyst.events \
  destination=explorer-queue \
  routing_key="catalyst.explorer.scan.request"

# Orchestrator listens to completion events
rabbitmqadmin declare binding \
  --vhost=$RABBITMQ_VHOST \
  --username=$RABBITMQ_USER \
  --password=$RABBITMQ_PASS \
  source=catalyst.events \
  destination=orchestrator-queue \
  routing_key="catalyst.*.complete"

echo "✅ RabbitMQ initialization complete!"
echo "   Exchange: catalyst.events (topic)"
echo "   Queues: 8 agent queues + 1 DLQ"
echo "   Bindings: Complete agent workflow"
