FROM public.ecr.aws/lambda/python:3.12

COPY proccess_frames/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./lambdas/

COPY proccess_frames/consolas.ttf ./lambdas/proccess_frames/consolas.ttf
COPY proccess_frames/lambda_function.py ./lambdas/proccess_frames/lambda_function.py
COPY proccess_frames/modules ./lambdas/proccess_frames/modules

CMD ["lambdas.proccess_frames.lambda_function.lambda_handler"]