import json
import os

import boto3
from slack_sdk.signature import SignatureVerifier

SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]
WORKER_TOPIC_ARN = os.environ["WORKER_TOPIC_ARN"]


def handler(event, context):
    try:
        request = json.loads(event["body"])

        print(request)

        # Events APIのリクエストURL登録時のチャレンジ認証を通すための処理
        # https://api.slack.com/events/url_verification
        if request["type"] == "url_verification":
            return {
                "statusCode": 200,
                "headers": {
                    "Content-type": "application/json",
                },
                "body": json.dumps(
                    {
                        "challenge": request["challenge"],
                    }
                ),
            }

        # Slackから送信されたリクエストであることを検証する
        # https://api.slack.com/authentication/verifying-requests-from-slack
        verifier = SignatureVerifier(SLACK_SIGNING_SECRET)
        if not verifier.is_valid_request(
            body=event["body"],
            headers=event["headers"],
        ):
            return {
                "statusCode": 400,
            }

        # 無限ループ回避のため、Botから送信されたメッセージであれば無視する
        if "bot_id" in request["event"]:
            return {
                "statusCode": 200,
            }

        # Amazon SNSにメッセージを公開し、後続のLambdaに処理を委譲する
        sns_client = boto3.client("sns")
        sns_client.publish(
            TopicArn=WORKER_TOPIC_ARN,
            Message=event["body"],
            MessageAttributes={
                "type": {
                    "DataType": "String",
                    "StringValue": request["event"]["type"],
                }
            },
        )

        return {
            "statusCode": 200,
        }
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")

        return {
            "statusCode": 500,
        }
