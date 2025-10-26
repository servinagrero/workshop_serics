#!/usr/bin/bash
#
# Obtain the NIST test suite

set -eu

git clone https://github.com/terrillmoore/NIST-Statistical-Test-Suite/tree/master

cd NIST-Statistical-Test-Suite || exit 1

./setup.sh
cd ./sts || exit 1
make

# Test input file
# Path to input file
# All tests
# Configuration
# 10 bitstreams
# 0 for ASCII and 1 for binary file
cat > config.txt << EOF
0
/path/to/bitstream.txt
1
0
10
0
EOF
