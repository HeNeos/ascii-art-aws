FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.12

RUN yum update --assumeyes && yum install ffmpeg libsm6 libxext6 libgl1 mesa-libGL ImageMagick ImageMagick-devel  -y

COPY downsize_video/requirements.txt .
RUN pip install --no-cache-dir -r ./requirements.txt

COPY *.py ./lambdas/
COPY downsize_video/lambda_function.py ./lambdas/downsize_video/lambda_function.py

CMD ["lambdas.downsize_video.lambda_function.lambda_handler"]