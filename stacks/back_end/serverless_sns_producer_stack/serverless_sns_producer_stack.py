from aws_cdk import aws_sns as _sns
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_iam as _iam
from aws_cdk import aws_logs as _logs
from aws_cdk import core as cdk
from stacks.miztiik_global_args import GlobalArgs


class ServerlessSnsProducerStack(cdk.Stack):
    def __init__(
        self, scope: cdk.Construct, construct_id: str, stack_log_level: str, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Add your stack resources below):
        # Create SNS Topic
        self.store_events_topic = _sns.Topic(
            self,
            "dataTopic",
            display_name="MessageFilterDemoTopic",
            topic_name=f"store_events_{construct_id}_topic"
        )

        ########################################
        #######                          #######
        #######   Stream Data Producer   #######
        #######                          #######
        ########################################

        # Read Lambda Code
        try:
            with open(
                "stacks/back_end/serverless_sns_producer_stack/lambda_src/stream_data_producer.py",
                encoding="utf-8",
                mode="r",
            ) as f:
                data_producer_fn_code = f.read()
        except OSError:
            print("Unable to read Lambda Function Code")
            raise

        data_producer_fn = _lambda.Function(
            self,
            "streamDataProducerFn",
            function_name=f"data_producer_{construct_id}",
            description="Produce streaming data events and push to SNS stream",
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.InlineCode(data_producer_fn_code),
            handler="index.lambda_handler",
            timeout=cdk.Duration.seconds(1),
            reserved_concurrent_executions=1,
            environment={
                "LOG_LEVEL": "INFO",
                "APP_ENV": "Production",
                "MAX_MSGS_TO_PRODUCE": "5",
                "TOPIC_ARN": f"{self.store_events_topic.topic_arn}",
                "TRIGGER_RANDOM_DELAY": "True"
            },
        )

        # Grant our Lambda Producer privileges to write to SNS Data Stream
        self.store_events_topic.grant_publish(data_producer_fn)

        data_producer_fn_version = data_producer_fn.latest_version
        data_producer_fn_version_alias = _lambda.Alias(
            self,
            "streamDataProducerFnAlias",
            alias_name="MystiqueAutomation",
            version=data_producer_fn_version,
        )

        # Create Custom Loggroup for Producer
        data_producer_lg = _logs.LogGroup(
            self,
            "streamDataProducerFnLogGroup",
            log_group_name=f"/aws/lambda/{data_producer_fn.function_name}",
            removal_policy=cdk.RemovalPolicy.DESTROY,
            retention=_logs.RetentionDays.ONE_DAY,
        )

        # Restrict Produce Lambda to be invoked only from the stack owner account
        data_producer_fn.add_permission(
            "restrictLambdaInvocationToOwnAccount",
            principal=_iam.AccountRootPrincipal(),
            action="lambda:InvokeFunction",
            source_account=cdk.Aws.ACCOUNT_ID,
            source_arn=self.store_events_topic.topic_arn
        )

        ###########################################
        ################# OUTPUTS #################
        ###########################################
        output_0 = cdk.CfnOutput(
            self,
            "AutomationFrom",
            value=f"{GlobalArgs.SOURCE_INFO}",
            description="To know more about this automation stack, check out our github page.",
        )

        output_1 = cdk.CfnOutput(
            self,
            "StoreOrdersEventsProducer",
            value=f"https://console.aws.amazon.com/lambda/home?region={cdk.Aws.REGION}#/functions/{data_producer_fn.function_name}",
            description="Produce streaming data events and push to SNS Topic.",
        )

    # properties to share with other stacks
    @property
    def get_topic(self):
        return self.store_events_topic
