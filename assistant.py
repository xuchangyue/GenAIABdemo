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
slack_token = "xoxb-1786157212486-7765839471783-ud2mi1wATeWpRjY8gT4s1S4l"
slack_client = WebClient(token=slack_token)
channel_id = "C07PBJVP0TT"
table = 'ai-profile'
claude_client = boto3.client("bedrock-runtime", region_name="us-east-1")
MODEL_ID= "anthropic.claude-3-5-sonnet-20240620-v1:0"



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

    system="You are acting like me on a dating app, be charming and natural living person", 
# Start a conversation with the user message.
    user_message = f"""Claude, I want you to act like me on a dating app, my user id is U01PATFNBEW, chat with my match, her user id is U07PB22SN2D.
    I want to impress her and make her find me attractive. 
    Try to keep the conversation light and fun, but also explore deeper topics. 
    And don't forget to be a bit naughty and dirty at times. 
    Stay in character at all times. 
    Keep the response short and to the point, no more than 20 words.

Here is our conversational history. It could be empty if there is no history:
<history>
{chat_history}
</history>
Here is my match's photo description and profile, you can get insight and have topic:
<profile>
{profile}
</profile>
"""
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
            additionalModelRequestFields={"top_k":250}
        )
        token_usage = response['usage']
        logger.info("Input tokens: %s", token_usage['inputTokens'])
        logger.info("Output tokens: %s", token_usage['outputTokens'])
        logger.info("Total tokens: %s", token_usage['totalTokens'])
        logger.info("Stop reason: %s", response['stopReason'])

    # Extract and print the response text.
        response_text = response["output"]["message"]["content"][0]["text"]
        return response_text
        print(response_text)

    except (ClientError, Exception) as e:
        print(f"ERROR: Can't invoke '{MODEL_ID}'. Reason: {e}")
        exit(1)


st.title('Get response')

if st.button('Generate response'):
    with st.spinner('Generating...'):
        result = chat_assistant(get_history(channel_id), get_profile(table, "Alice"))
        st.write(result)


