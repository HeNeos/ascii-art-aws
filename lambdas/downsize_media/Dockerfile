FROM public.ecr.aws/lambda/python:3.12

COPY downsize_media/requirements.txt .
RUN pip install --no-cache-dir -r ./requirements.txt

COPY *.py ./lambdas/

COPY downsize_media/lambda_function.py ./lambdas/downsize_media/lambda_function.py

CMD ["lambdas.downsize_media.lambda_function.lambda_handler"]
