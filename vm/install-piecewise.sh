#!/bin/bash

PROJECT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
docker_img_path="${PROJECT_PATH}/binaries/piece-wise.docker"

if [[ ! -f $docker_img_path ]]; then

    FILEID="1-7gYC63Aaps7KGkGgWisEF_96ChxI9jV"
    confirm_id=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate "https://docs.google.com/uc?export=download&id=${FILEID}" -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')

    echo "Downloading docker image from GoogleDrive "
    wget --load-cookies /tmp/cookies.txt \
        "https://docs.google.com/uc?export=download&confirm=${confirm_id}&id=${FILEID}" \
        -O "${docker_img_path}"

    test -f /tmp/cookies.txt && rm -rf /tmp/cookies.txt
fi

echo "Loading piecewise docker image"
sudo docker load --input "${PROJECT_PATH}/binaries/piece-wise.docker"
