#!/usr/bin/env bash

# Copyright (c) 2022 SRI International All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

#arguments for input
TOOL=$1
CONFIG_FILE=$2
INVOKE_CMD=$3
ADAPTER_SCRIPT_PATH=$4
BINARIES_OUTPUT_LOCAL=$5
BINARIES_OUTPUT_CONTAINER=$6
RUNTIME=0

#Sending config file to the tool specific container and invoking adapter script there
mkdir -p $BINARIES_OUTPUT_LOCAL
CONTAINER=$(docker run -itd $TOOL)
docker cp $CONFIG_FILE $CONTAINER:/$CONFIG_FILE
time1=$EPOCHSECONDS
docker exec -it $CONTAINER $INVOKE_CMD $ADAPTER_SCRIPT_PATH $CONFIG_FILE 
time2=$EPOCHSECONDS
RUNTIME=$((time2-time1))
#Fetching output binary to the local specified path
BINARIES_LOCAL_PATH_TIMED=$BINARIES_OUTPUT_LOCAL/result-$(date | cut -d ' ' -f 2,3,4,5 | sed -e "s/ /-/g" | sed -e "s/:/./g")
mkdir -p $BINARIES_LOCAL_PATH_TIMED
docker cp $CONTAINER:$BINARIES_OUTPUT_CONTAINER/. "$BINARIES_LOCAL_PATH_TIMED/" 
if [[ $? == 0 ]]; then 
	echo "Binary copied to $BINARIES_LOCAL_PATH_TIMED/"
	echo "Runtime: "$RUNTIME "seconds";echo -e '\n'
# running metrics evaluation
	bash sources/evaluation.sh $BINARIES_LOCAL_PATH_TIMED
else
	echo "Error Encountered"
fi

#winding down
docker kill $CONTAINER >&/dev/null
