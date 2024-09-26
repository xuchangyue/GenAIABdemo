import streamlit as st
import boto3
from botocore.exceptions import NoCredentialsError
import io

# 设置AWS凭证（请替换为你自己的凭证）

BUCKET_NAME = 'xucy-us-east-1'

# 创建S3客户端
s3 = boto3.client('s3')

def upload_to_s3(file_bytes, bucket, s3_file):
    try:
        s3.upload_fileobj(file_bytes, bucket, s3_file)
        return True
    except NoCredentialsError:
        st.error("凭证无效。请检查您的AWS凭证。")
        return False
    except Exception as e:
        st.error(f"上传过程中发生错误: {str(e)}")
        return False

st.title('上传图片到S3')

uploaded_file = st.file_uploader("选择一个图片文件", type=['png', 'jpg', 'jpeg'])

if uploaded_file is not None:
    if st.button('上传到S3'):
        file_name = uploaded_file.name
        file_bytes = io.BytesIO(uploaded_file.getvalue())
        with st.spinner('正在上传...'):
            if upload_to_s3(file_bytes, BUCKET_NAME, file_name):
                st.success(f'文件 {file_name} 已成功上传到S3!')
            else:
                st.error('上传失败。')

    st.image(uploaded_file, caption='预览上传的图片', use_column_width=True)