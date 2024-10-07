FROM public.ecr.aws/lambda/python:3.12

COPY merge_frames/requirements.txt .
RUN pip install --no-cache-dir -r ./requirements.txt

COPY *.py ./lambdas/
COPY merge_frames/*.py ./lambdas/merge_frames/.

CMD ["lambdas.merge_frames.lambda_function.lambda_handler"]
