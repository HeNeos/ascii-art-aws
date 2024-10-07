# lambda/downsize_media/Dockerfile
FROM public.ecr.aws/lambda/python:3.12

# Copy requirements and function code
COPY extract_audio/requirements.txt ./
COPY extract_audio/lambda_function.py ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Command to run the Lambda function
CMD ["lambda_function.lambda_handler"]
