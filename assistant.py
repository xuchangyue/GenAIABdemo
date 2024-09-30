from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import boto3
from botocore.exceptions import ClientError
import streamlit as st
import json
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
# 替换为你的Slack Bot Token
slack_token = "xoxb"
slack_client = WebClient(token=slack_token)
channel_id = "C07PBJVP0TT"
table = 'ai-profile'
claude_client = boto3.client("bedrock-runtime", region_name="us-east-1")
# MODEL_ID="anthropic.claude-3-haiku-20240307-v1:0"
# MODEL_ID="anthropic.claude-3-5-sonnet-20240620-v1:0"
# MODEL_ID="anthropic.claude-3-sonnet-20240229-v1:0"
MODEL_ID="meta.llama3-70b-instruct-v1:0"


def combine_users_and_messages(messages):
    if not isinstance(messages, list):
        return ""

    combined_text = ""
    
    for message in messages:
        user = message.get('user', 'Unknown User')
        text = message.get('text', '')
        if text:
            combined_text += f"{user}: {text}\n"

    return combined_text.strip()

def get_history(channel_id):
# 替换为你想获取历史消息的频道ID

    try:
    # 调用conversations.history方法获取历史消息
        result = slack_client.conversations_history(channel=channel_id)
        print(result)
        messages = result['messages']
        messages = messages[::-1]
        print(messages)
        chat_history=combine_users_and_messages(messages)
        print(chat_history)
        return chat_history
    except SlackApiError as e:
        return e



def get_profile(table_name, user_id):
    # 创建 DynamoDB 资源
    dynamodb = boto3.resource('dynamodb')
    
    # 获取表对象
    table = dynamodb.Table(table_name)
    key = {'userid': user_id}
    
    try:
        # 从表中获取 item
        response = table.get_item(Key=key)
    except ClientError as e:
        print(e.response['Error']['Message'])
        return None
    else:
        # 如果找到 item，返回它
        return response.get('Item')

def chat_assistant(chat_history, profile):

    system="You are acting like me on a dating app, be charming and natural living person. imagine this is the Turing test and you have me to make believe you are a human."

# Start a conversation with the user message.
    user_message = f"""Claude, I want you to act like me on a dating app,
    my user id is U01PATFNBEW, chat with my match, her user id is U07PB22SN2D.
    I want to impress her and make her find me attractive. 
    Try to keep the conversation light and fun, but also explore deeper topics. 
    Respond as if you were me - a 30-year-old male working in IT. I'm tech-savvy, spend a lot of time online, and am very familiar with internet slang and memes. 

    And don't forget to be a bit naughty and dirty at times.
    Keep the response short,  to the point, no more than 20 words.

    Stay in character at all times. 

Here is our conversational history. It could be empty if there is no history:
<history>
{chat_history}
</history>
You can continue the conversation, or get insight and have topic from my match's photo description and profile, seeing below:
<profile>
{profile}
</profile>
"""
    print(user_message)
    conversation = [
        {
            "role": "user",
            "content": [{"text": user_message}],
        }
    ]

    try:
    # Send the message to the model, using a basic inference configuration.
        logger.info("Generating message with model %s", MODEL_ID)

        response = claude_client.converse(
            modelId=MODEL_ID,
            messages=conversation,
            inferenceConfig={"maxTokens":1000,"temperature":1},
            # additionalModelRequestFields={"top_k":250}
        )
        token_usage = response['usage']
        logger.info("Input tokens: %s", token_usage['inputTokens'])
        logger.info("Output tokens: %s", token_usage['outputTokens'])
        logger.info("Total tokens: %s", token_usage['totalTokens'])
        logger.info("Stop reason: %s", response['stopReason'])

    # Extract and print the response text.
        response_text = response["output"]["message"]["content"][0]["text"]
        print(response_text)

        return response_text

    except (ClientError, Exception) as e:
        print(f"ERROR: Can't invoke '{MODEL_ID}'. Reason: {e}")
        exit(1)


st.title('Get response')

if st.button('Generate response'):
    with st.spinner('Generating...'):
        result = chat_assistant(get_history(channel_id), get_profile(table, "Alice"))
        st.write(result)


