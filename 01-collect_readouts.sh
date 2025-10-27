#!/usr/bin/bash
#
# Erase the flash and obtain a single SRAM readout

set -eu

READOUTS_DIR="data/<group number>"
mkdir -p "${READOUTS_DIR}"

echo "Mass erasing the flash"
python3 openocd_stm32.py \
    --openocd-scripts "OpenOCD/tcl" \
    --interface "interface/stlink.cfg" --target="board/stm32ldiscovery.cfg" \
    flash --erase

echo "Reading out SRAM"
python3 openocd_stm32.py \
    --openocd-scripts "OpenOCD/tcl" \
    --interface "interface/stlink.cfg" --target="board/stm32ldiscovery.cfg" \
    read --address 0x20000000 --size 0x8000 --dir "${READOUTS_DIR}"
