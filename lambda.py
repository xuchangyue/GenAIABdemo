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

def lambda_handler(event):
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
        logger.info("Input tokens: %s", token_usage['inputTokens'])
        logger.info("Output tokens: %s", token_usage['outputTokens'])
        logger.info("Total tokens: %s", token_usage['totalTokens'])
        logger.info("Stop reason: %s", response['stopReason'])

        response_text = response["output"]["message"]["content"][0]["text"]
        
        # 将结果存储到 DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        table.put_item(
            Item={
                'userid':"bob",
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
event ={
  "Records": [
    {
      "eventVersion": "2.0",
      "eventSource": "aws:s3",
      "awsRegion": "us-east-1",
      "eventTime": "1970-01-01T00:00:00.000Z",
      "eventName": "ObjectCreated:Put",
      "userIdentity": {
        "principalId": "EXAMPLE"
      },
      "requestParameters": {
        "sourceIPAddress": "127.0.0.1"
      },
      "responseElements": {
        "x-amz-request-id": "EXAMPLE123456789",
        "x-amz-id-2": "EXAMPLE123/5678abcdefghijklambdaisawesome/mnopqrstuvwxyzABCDEFGH"
      },
      "s3": {
        "s3SchemaVersion": "1.0",
        "configurationId": "testConfigRule",
        "bucket": {
          "name": "xucy-us-east-1",
          "ownerIdentity": {
            "principalId": "EXAMPLE"
          },
          "arn": "arn:aws:s3:::example-bucket"
        },
        "object": {
          "key": "20240709-095118.jpeg",
          "size": 1024,
          "eTag": "0123456789abcdef0123456789abcdef",
          "sequencer": "0A1B2C3D4E5F678901"
        }
      }
    }
  ]
}
lambda_handler(event)

