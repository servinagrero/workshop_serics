#!/usr/bin/env bash

set -eu

# Technically, we don't need the whole repository, just the TCL scripts
# For now we stick with this lazy solution
git clone https://github.com/STMicroelectronics/OpenOCD.git

# If there is no openocd in the system wide installation, we install it from here
if ! command -v "openocd"
then
    cd OpenOCD || exit 1
    ./bootstrap
    ./configure
    make
    sudo make install
fi
