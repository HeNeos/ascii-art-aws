FROM public.ecr.aws/lambda/python:3.12

RUN dnf update -y && \
  dnf install -y \
  python3-devel \
  gcc \
  cairo \
  cairo-devel \
  pkgconfig \
  gcc

COPY extract_audio/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./lambdas/
COPY extract_audio/lambda_function.py ./lambdas/extract_audio/lambda_function.py

CMD ["lambdas.extract_audio.lambda_function.lambda_handler"]
