import json
import logging
import datetime
import os
import random
import uuid

import boto3


class GlobalArgs:
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    MAX_MSGS_TO_PRODUCE = int(os.getenv("MAX_MSGS_TO_PRODUCE", 5))
    TOPIC_ARN = os.getenv("TOPIC_ARN")


def set_logging(lv=GlobalArgs.LOG_LEVEL):
    logging.basicConfig(level=lv)
    logger = logging.getLogger()
    logger.setLevel(lv)
    return logger


logger = set_logging()


def _rand_coin_flip():
    r = False
    if os.getenv("TRIGGER_RANDOM_FAILURES", True):
        if random.randint(1, 100) > 90:
            r = True
    return r


def _gen_uuid():
    return str(uuid.uuid4())


def send_data(client, data, _attr, t_arn):
    logger.info(
        f'{{"data":{json.dumps(data)}}}')
    resp = client.publish(
        TopicArn=t_arn,
        Message=json.dumps(data),
        MessageAttributes=_attr
    )
    logger.debug(f"Response:{resp}")


client = boto3.client("sns")


def lambda_handler(event, context):
    resp = {"status": False}
    logger.debug(f"Event: {json.dumps(event)}")

    _usr_names = ["Aarakocra", "Aasimar", "Githzerai", "Gnoll", "Gnome", "Goblin", "Goliath", "Hag", "Half-Elf",
                  "Half-Orc", "Halfling"]

    _categories = ["Books", "Games", "Mobiles", "Groceries", "Shoes", "Stationaries", "Laptops",
                   "Tablets", "Notebooks", "Camera", "Printers", "Monitors", "Speakers", "Projectors", "Cables", "Furniture"]

    _evnt_types = ["sales-event", "inventory-event"]

    try:
        t_msgs = 0
        p_cnt = 0
        s_evnts = 0
        inventory_evnts = 0
        t_sales = 0
        while context.get_remaining_time_in_millis() > 100:
            _s = round(random.random() * 100, 2)
            _evnt_type = random.choice(_evnt_types)
            _u = _gen_uuid()
            p_s = bool(random.getrandbits(1))
            evnt_body = {
                "request_id": _u,
                "name": random.choice(_usr_names),
                "category": random.choice(_categories),
                "store_id": random.randint(1, 10),
                "evnt_time": datetime.datetime.now().isoformat(),
                "evnt_type": _evnt_type,
                "new_order": True,
                "sales": _s,
                "sku": random.randint(18981, 189281),
                "gift_wrap": bool(random.getrandbits(1)),
                "qty": random.randint(1, 38),
                "priority_shipping": p_s,
                "contact_me": "github.com/miztiik"
            }
            evnt_attr = {
                "evnt_type": {
                    "DataType": "String",
                    "StringValue": _evnt_type
                },
                "priority_shipping": {
                    "DataType": "String",
                    "StringValue": f"{p_s}"
                }
            }

            # Randomly make the return type order
            if bool(random.getrandbits(1)):
                evnt_body.pop("new_order", None)
                evnt_body["is_return"] = True

            if _rand_coin_flip():
                evnt_body.pop("store_id", None)
                evnt_body["bad_msg"] = True
                p_cnt += 1

            if _evnt_type == "sales-event":
                s_evnts += 1
            elif _evnt_type == "inventory-event":
                inventory_evnts += 1

            send_data(
                client,
                evnt_body,
                evnt_attr,
                GlobalArgs.TOPIC_ARN
            )
            t_msgs += 1
            t_sales += _s

        resp["tot_msgs"] = t_msgs
        resp["bad_msgs"] = p_cnt
        resp["sales_evnts"] = s_evnts
        resp["inventory_evnts"] = inventory_evnts
        resp["tot_sales"] = t_sales
        resp["status"] = True
        logger.info(f'{{"resp":{json.dumps(resp)}}}')

    except Exception as e:
        logger.error(f"ERROR:{str(e)}")
        resp["err_msg"] = str(e)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": resp
        })
    }
