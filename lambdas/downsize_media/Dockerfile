# Stage 1: Build stage
FROM public.ecr.aws/lambda/python:3.12 AS builder

RUN dnf install -y python3-devel gcc pkg-config

COPY downsize_media/requirements.txt .
RUN pip install --no-cache-dir --target /deps -r ./requirements.txt

# Stage 2: Final image
FROM public.ecr.aws/lambda/python:3.12

COPY --from=builder /deps /var/lang/lib/python3.12/site-packages

COPY __init__.py ./lambdas/
COPY utils/*.py ./lambdas/utils/
COPY models/*.py ./lambdas/models/
COPY clients/*.py ./lambdas/clients/
COPY downsize_media/lambda_function.py ./lambdas/downsize_media/lambda_function.py

CMD ["lambdas.downsize_media.lambda_function.lambda_handler"]