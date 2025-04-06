FROM public.ecr.aws/lambda/provided:al2023

RUN dnf update -y && \
  dnf install -y \
  python3.11 \
  python3.11-pip \
  python3.11-devel \
  gcc \
  pkgconfig \
  git \
  unzip \
  xz \
  wget \
  tar

RUN wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz && \
  tar -xf ffmpeg-release-arm64-static.tar.xz --strip-components=1 -C /usr/local/bin && \
  ln -sf /usr/local/bin/ffmpeg /usr/bin/ffmpeg && \
  rm -f ffmpeg-release-arm64-static.tar.xz


RUN pip3.11 install awslambdaric
ENTRYPOINT ["python3.11", "-m", "awslambdaric"]


COPY extract_audio/requirements.txt .
RUN pip3.11 install --no-cache-dir -r ./requirements.txt

COPY __init__.py ./lambdas/

COPY utils/*.py ./lambdas/utils/
COPY extract_audio/lambda_function.py ./lambdas/extract_audio/lambda_function.py

CMD ["lambdas.extract_audio.lambda_function.lambda_handler"]
