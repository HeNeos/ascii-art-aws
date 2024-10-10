FROM public.ecr.aws/lambda/python:3.12

COPY process_frames/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./lambdas/

COPY process_frames/consolas.ttf .
COPY process_frames/lambda_function.py ./lambdas/process_frames/lambda_function.py
COPY process_frames/modules ./lambdas/process_frames/modules

CMD ["lambdas.process_frames.lambda_function.lambda_handler"]