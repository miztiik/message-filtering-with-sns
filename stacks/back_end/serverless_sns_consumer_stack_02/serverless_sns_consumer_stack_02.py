from aws_cdk import aws_iam as _iam
from aws_cdk import aws_sqs as _sqs
from aws_cdk import aws_sns as _sns
from aws_cdk import aws_sns_subscriptions as _sns_subs
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_logs as _logs
from aws_cdk.aws_lambda_event_sources import SqsEventSource as _sqsEventSource
from aws_cdk import core as cdk
from stacks.miztiik_global_args import GlobalArgs


class ServerlessSnsConsumer02Stack(cdk.Stack):

    def __init__(
        self,
        scope: cdk.Construct,
        construct_id: str,
        stack_log_level: str,
        store_events_topic,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Add your stack resources below)

        # Inventory Queue Consumer
        inventory_q = _sqs.Queue(
            self,
            "inventoryEventsQueue",
            delivery_delay=cdk.Duration.seconds(5),
            queue_name=f"inventory_q",
            retention_period=cdk.Duration.days(2),
            visibility_timeout=cdk.Duration.seconds(10),
            receive_message_wait_time=cdk.Duration.seconds(10)
        )

        # Create a Filter for inventory Subscription
        inventory_policy = {
            "evnt_type": _sns.SubscriptionFilter(conditions=["inventory-event"])
        }

        # Create an SQS type subscription to SNS
        inventory_subs = _sns_subs.SqsSubscription(
            inventory_q,
            filter_policy=inventory_policy
        )

        # Add the scription to topic
        store_events_topic.add_subscription(
            inventory_subs

        )

        # Read Lambda Code
        try:
            with open("stacks/back_end/serverless_sns_consumer_stack/lambda_src/sqs_data_consumer.py",
                      encoding="utf-8",
                      mode="r"
                      ) as f:
                msg_consumer_fn_code = f.read()
        except OSError:
            print("Unable to read Lambda Function Code")
            raise
        msg_consumer_fn = _lambda.Function(
            self,
            "msgConsumerFn",
            function_name=f"inventory_q_consumer_fn",
            description="Process messages in SQS queue",
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.InlineCode(
                msg_consumer_fn_code),
            handler="index.lambda_handler",
            timeout=cdk.Duration.seconds(5),
            reserved_concurrent_executions=1,
            environment={
                "LOG_LEVEL": f"{stack_log_level}",
                "APP_ENV": "Production",
                "INVENTORY_QUEUE_NAME": f"{inventory_q.queue_name}",
                "TRIGGER_RANDOM_DELAY": "True"
            }
        )

        msg_consumer_fn_version = msg_consumer_fn.latest_version
        msg_consumer_fn_version_alias = _lambda.Alias(
            self,
            "msgConsumerFnAlias",
            alias_name="MystiqueAutomation",
            version=msg_consumer_fn_version
        )

        # Create Custom Loggroup for Producer
        msg_consumer_fn_lg = _logs.LogGroup(
            self,
            "msgConsumerFnLogGroup",
            log_group_name=f"/aws/lambda/{msg_consumer_fn.function_name}",
            removal_policy=cdk.RemovalPolicy.DESTROY,
            retention=_logs.RetentionDays.ONE_DAY
        )

        # Restrict Produce Lambda to be invoked only from the stack owner account
        msg_consumer_fn.add_permission(
            "restrictLambdaInvocationToOwnAccount",
            principal=_iam.AccountRootPrincipal(),
            action="lambda:InvokeFunction",
            source_account=cdk.Aws.ACCOUNT_ID,
            source_arn=inventory_q.queue_arn
        )

        # Set our Lambda Function to be invoked by SQS
        msg_consumer_fn.add_event_source(
            _sqsEventSource(inventory_q, batch_size=5))

        ###########################################
        ################# OUTPUTS #################
        ###########################################
        output_0 = cdk.CfnOutput(
            self,
            "AutomationFrom",
            value=f"{GlobalArgs.SOURCE_INFO}",
            description="To know more about this automation stack, check out our github page."
        )

        output_2 = cdk.CfnOutput(
            self,
            "InventoryEventsConsumer",
            value=f"https://console.aws.amazon.com/lambda/home?region={cdk.Aws.REGION}#/functions/{msg_consumer_fn.function_name}",
            description="Process events received from SQS event bus"
        )
