# Stage 1: Build stage
FROM public.ecr.aws/lambda/provided:al2023 as builder

RUN dnf update -y && \
  dnf install -y \
  python3.11 \
  python3.11-pip \
  python3.11-devel \
  gcc \
  wget \
  xz \
  tar \
  && dnf clean all

RUN wget https://github.com/HeNeos/ascii-art-aws/blob/dev/ffmpeg-release-arm64-static.tar.xz && \
  tar -xf ffmpeg-release-arm64-static.tar.xz --strip-components=1 -C /usr/local/bin && \
  rm ffmpeg-release-arm64-static.tar.xz

COPY extract_audio/requirements.txt .
RUN pip3.11 install --no-cache-dir --target /deps awslambdaric -r requirements.txt

# Stage 2: Final image
FROM public.ecr.aws/lambda/provided:al2023

RUN dnf update -y && \
  dnf install -y \
  python3.11 \
  && dnf clean all

COPY --from=builder /usr/local/bin/ffmpeg /usr/local/bin/ffmpeg
COPY --from=builder /deps /usr/local/lib/python3.11/site-packages

COPY __init__.py ./lambdas/
COPY utils/*.py ./lambdas/utils/
COPY extract_audio/lambda_function.py ./lambdas/extract_audio/lambda_function.py

ENTRYPOINT ["python3.11", "-m", "awslambdaric"]
CMD ["lambdas.extract_audio.lambda_function.lambda_handler"]
