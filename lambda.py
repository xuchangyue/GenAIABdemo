import json
import boto3
from io import BytesIO
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
# 初始化 AWS 服务客户端
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
bedrock = boto3.client('bedrock-runtime')
MODEL_ID = "anthropic.claude-3-5-sonnet-20240620-v1:0"

# 指定 DynamoDB 表名
TABLE_NAME = 'ai-profile'

def lambda_handler(event, context):
    # 从 S3 事件中获取桶名和对象键
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    try:
        # 从 S3 下载图像
        response = s3.get_object(Bucket=bucket, Key=key)
        image_content = response['Body'].read()
        
        # 准备 Bedrock 请求体
        user_message = "This ia a photo uploaded to a dating app from a user, describe this picture and get insight from it."

        messages = [
            {
                "role": "user",
                "content": [
                {"image": {"format": "png", "source": {"bytes": image_content}}},
                {"text": user_message},
            ],
            }
        ]   
        logger.info("Generating message with model %s", MODEL_ID)
        response = bedrock.converse(
            modelId=MODEL_ID,
            messages=messages,
            inferenceConfig={"maxTokens":1000,"temperature":1},
            additionalModelRequestFields={"top_k":250}
            )
        token_usage = response['usage']
        print("Input tokens:", token_usage['inputTokens'])
        print("Output tokens:",token_usage['outputTokens'])
        print("Total tokens:", token_usage['totalTokens'])
        print("Stop reason:", response['stopReason'])

        response_text = response["output"]["message"]["content"][0]["text"]
        
        # 将结果存储到 DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        table.put_item(
            Item={
                'userid':"Alice",
                'ImageKey': key,
                'Description': response_text
            }
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps('Image processed and result stored successfully')
        }
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error processing image: {str(e)}')
        }