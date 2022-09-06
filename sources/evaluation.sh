#!/usr/bin/env bash

# Copyright (c) 2022 SRI International All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

BINARY_DIR=$1
echo -e 'Metrics Results\n'
for file in $(ls $BINARY_DIR/*);do
	echo 'File:' $file
	rop_gadget_count=$(ROPgadget --binary $file | grep 'Unique' | cut -d ' ' -f 4)
	size=$(ls -l $file | cut -d ' ' -f 5)
	echo 'Unique ROP gadgets: '$rop_gadget_count;
	echo 'Size: '$size 'bytes';echo -e '\n';
done;
