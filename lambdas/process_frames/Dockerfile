FROM public.ecr.aws/lambda/python:3.12

RUN dnf update -y && \
  dnf install -y \
  python3-devel \
  gcc \
  cairo \
  cairo-devel \
  pkgconfig \
  gcc

COPY process_frames/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./lambdas/

COPY process_frames/consolas.ttf .
COPY process_frames/lambda_function.py ./lambdas/process_frames/lambda_function.py
COPY process_frames/modules ./lambdas/process_frames/modules

CMD ["lambdas.process_frames.lambda_function.lambda_handler"]