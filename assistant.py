from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import boto3
from botocore.exceptions import ClientError
import streamlit as st
import json
# 替换为你的Slack Bot Token
slack_token = "xoxb-1786157212486-7765839471783-ud2mi1wATeWpRjY8gT4s1S4l"
slack_client = WebClient(token=slack_token)
channel_id = "C07PBJVP0TT"
table = 'ai-profile'
claude_client = boto3.client("bedrock-runtime", region_name="us-east-1")



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

    model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    system="You are an AI verson of me on a dating app, chatting with my match.", 
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
Here is my match's photo description and profile, you can get insight in this picture and have topic:
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
        response = claude_client.converse(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            messages=conversation,
            inferenceConfig={"maxTokens":1000,"temperature":1},
            additionalModelRequestFields={"top_k":250}
        )

    # Extract and print the response text.
        response_text = response["output"]["message"]["content"][0]["text"]
        return response_text
        print(response_text)

    except (ClientError, Exception) as e:
        print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
        exit(1)


st.title('Get response')

if st.button('Generate response'):
    with st.spinner('Generating...'):
        result = chat_assistant(get_history(channel_id), get_profile(table, "Alice"))
        st.write(result)


# st.title("Dating Coach Joe")

# # 初始化聊天历史
# if "messages" not in st.session_state:
#     st.session_state.messages = []

# 显示聊天历史
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])

# # 用户输入
# if prompt := st.chat_input("How is it going?"):
#     # 添加用户消息到聊天历史
#     st.session_state.messages.append({"role": "user", "content": prompt})
#     with st.chat_message("user"):
#         st.markdown(prompt)

#     # 调用 Claude 3.5
#     try:
#         assistant_response=chat_assistant(get_history(channel_id), get_profile(table, "bob"), prompt)
#         # 添加助手回复到聊天历史
#         st.session_state.messages.append({"role": "assistant", "content": assistant_response})
#         print(assistant_response)
#         with st.chat_message("assistant"):
#             st.markdown(assistant_response)

#     except ClientError as e:
#         st.error(f"发生错误: {e}")

