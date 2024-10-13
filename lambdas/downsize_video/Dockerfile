FROM public.ecr.aws/lambda/provided:al2023

RUN dnf update -y && \
  dnf install -y \
  python3.11 \
  python3.11-pip \
  gcc \
  git \
  unzip \
  xz \
  wget \
  tar

RUN wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz && \
  tar -xf ffmpeg-release-amd64-static.tar.xz --strip-components=1 -C /usr/local/bin && \
  ln -sf /usr/local/bin/ffmpeg /usr/bin/ffmpeg && \
  rm -f ffmpeg-release-amd64-static.tar.xz

RUN pip3.11 install awslambdaric
ENTRYPOINT ["python3.11", "-m", "awslambdaric"]

COPY downsize_video/requirements.txt .
RUN pip3.11 install --no-cache-dir -r ./requirements.txt

COPY *.py ./lambdas/
COPY downsize_video/lambda_function.py ./lambdas/downsize_video/lambda_function.py

CMD ["lambdas.downsize_video.lambda_function.lambda_handler"]