# ascii-art-aws

## Architecture diagram

![architecture diagram](https://raw.githubusercontent.com/HeNeos/ascii-art-aws/main/ascii_art.drawio.png)

## Description

It mostly works for images, in less than 10 sec, be aware that image resolution is big and could be heavier.

Videos also work, but due to storage limitations it's resized to low quality, bitrate is also capped to a decent value but h264 is not a good encoder for the ascii frames so ascii videos are heavier, you can expect to have a resolution >720p for them.

It should work for any video <3 min and <50MB.

Even when it's possible to process a higher resolution with a higher bitrate, there a few bottlenecks:

1. Storage: A higher resolution and a higher bitrate could lead to heavier videos, currently I was able to see ascii videos up to 300MB for less than 4 min, so I'm not planning to increase these values. If you want higher resolution ascii images, try with the frames, since the image processing has higher limits.

2. Memory: I'm using Lambda Functions, and it has a memory limit of 10240MB, so longer and heavy videos are not allowed.

TODO: 
  - Process videos without audio.
  - Implement API GW (lambda URL for videos, API GW for images)
  - Lifecycle policy S3