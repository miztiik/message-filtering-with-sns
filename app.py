#!/usr/bin/env python3

from stacks.back_end.serverless_sns_producer_stack.serverless_sns_producer_stack import ServerlessSnsProducerStack
from stacks.back_end.serverless_sns_consumer_stack.serverless_sns_consumer_stack import ServerlessSnsConsumerStack
from stacks.back_end.serverless_sns_consumer_stack_02.serverless_sns_consumer_stack_02 import ServerlessSnsConsumer02Stack
from aws_cdk import core as cdk

app = cdk.App()

# SNS Data Producer on Lambda
serverless_sns_producer_stack = ServerlessSnsProducerStack(
    app,
    f"{app.node.try_get_context('project')}-producer-stack",
    stack_log_level="INFO",
    description="Miztiik Automation: SNS Data Producer on Lambda"
)


# Filter Sales Events in SNS and send to appropriate sqs/lambda consumer
sales_events_consumer_stack = ServerlessSnsConsumerStack(
    app,
    f"{app.node.try_get_context('project')}-sales-consumer-stack",
    stack_log_level="INFO",
    store_events_topic=serverless_sns_producer_stack.get_topic,
    description="Miztiik Automation: Filter Sales Events in SNS and send to appropriate sqs/lambda consumer"
)

# Filter Inventory Events in SNS and send to appropriate sqs/lambda consumer
inventory_events_consumer_stack = ServerlessSnsConsumer02Stack(
    app,
    f"{app.node.try_get_context('project')}-inventory-consumer-stack",
    stack_log_level="INFO",
    store_events_topic=serverless_sns_producer_stack.get_topic,
    description="Miztiik Automation: Filter Inventory Events in SNS and send to appropriate sqs/lambda consumer"
)


# Stack Level Tagging
_tags_lst = app.node.try_get_context("tags")

if _tags_lst:
    for _t in _tags_lst:
        for k, v in _t.items():
            cdk.Tags.of(app).add(k, v, apply_to_launched_instances=True)

app.synth()
