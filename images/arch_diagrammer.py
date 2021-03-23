from diagrams import Cluster,Diagram
from diagrams.aws.integration import SimpleQueueServiceSqs as _sqs
from diagrams.aws.integration import SimpleNotificationServiceSns as _sns
from diagrams.aws.compute import Lambda as _lambda

# from aws_cdk import aws_sns_subscriptions as _sns_subs


with Diagram("MiztiikUnicorn Event Driven Architecture", show=False):
    # _sns("store events producer") >> [ _sqs("sales-event"), _sqs("inventory-event")]

    # with Cluster("SQS Subscriptions"):
    #     svc_group = [_sqs("sales-event"),
    #                  _sqs("inventory-event")
    #                  ]
    _sns("store events producer") >> _sqs("sales-event") >> _lambda("consumer")
    # >> _lambda("consumer1") >>  >> _lambda("consumer2")