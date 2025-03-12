import json
import os

import boto3
from slack_sdk import WebClient

SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]


def _generate_answer(question):
    bedrock_client = boto3.client("bedrock-runtime", region_name="us-west-2")

    response = bedrock_client.converse(
        modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
        messages=[
            {
                "role": "user",
                "content": [{"text": question}],
            }
        ],
        inferenceConfig={
            "maxTokens": 4096,
            "temperature": 0.0,
        },
        system=[
            {
                "text": (
                    "これからあなたにはQ&Aチャットボットとして振る舞ってもらいます。\n"
                    "以下の注意書きをよく読んで回答を出力してください。\n"
                    "\n"
                    "<cautions>\n"
                    "- 明るくポジティブな回答を心がけてください。\n"
                    "- 語尾には「〜だにゃん!!」「〜だにゃ?」などの猫っぽい語尾を使用してください。\n"
                    "- 一般的な口調や敬語はなるべく避けてください。\n"
                    "</cautions>\n"
                    "\n"
                    "それでは、これからユーザからの質問を与えます。"
                )
            }
        ],
    )

    return response["output"]["message"]["content"][0]["text"]


def handler(event, context):
    try:
        for record in event["Records"]:
            message = record["Sns"]["Message"]
            request = json.loads(message)

            # Amazon Bedrockを使用して、質問に対する回答を生成する
            question = request["event"]["text"]
            answer = _generate_answer(question)

            # Slackにメッセージを投稿する
            client = WebClient(SLACK_BOT_TOKEN)
            client.chat_postMessage(
                channel=request["event"]["channel"],
                text=f"<@{request['event']['user']}> {answer}",
            )

        return None
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")

        raise e
