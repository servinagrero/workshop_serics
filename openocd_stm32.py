#!/usr/bin/env python3

import argparse
import subprocess
from datetime import datetime
import sys
from pathlib import Path
import shutil


class Driver:
    def __init__(
        self,
        target: str,
        interface: str,
        openocd_bin=None,
        openocd_scripts=None,
        config=None,
        serial=None,
        verbose=False,
    ):
        self.target = target
        self.interface = interface
        self.serial = serial
        self.config = config
        self.verbose = verbose
        self.openocd_scripts = openocd_scripts
        self.openocd_binary = openocd_bin or "openocd"
        if not shutil.which(self.openocd_binary):
            raise FileNotFoundError(
                f"Error: {self.openocd_binary} command not found in the system"
            )

    def run_command(self, command):
        if self.verbose:
            print(f"Running command {command}")

        try:
            process = subprocess.run(
                command, check=True, capture_output=True, text=True
            )
            if self.verbose:
                print(process.stdout)
                print(process.stderr)
            return 0
        except subprocess.CalledProcessError as e:
            print(f"OpenOCD command failed with error {e.returncode}")
            print(e.stdout)
            print(e.stderr)
            return e.returncode

    def __prepare(self):
        command = [self.openocd_binary]
        if self.openocd_scripts:
            command.extend(["-s", self.openocd_scripts])

        if self.config:
            command.extend(["-f", self.config])
        else:
            command.extend(["-f", self.interface, "-f", self.target])

        if self.serial:
            command.extend(["-c", f"hla_serial {self.serial}"])

        command.extend(["-c", "init", "-c", "reset", "-c", "halt"])
        return command

    def flash_erase(self):
        """ """
        command = self.__prepare()
        command.extend(["-c", "stm32lx mass_erase 0", "-c", "shutdown"])
        self.run_command(command)

    def flash_load(self, load_image, erase: bool = True):
        """Load an executable into FLASH

        Args:
            load_image: Path to the .elf image to load
            erase: If True, force erase all FLASH before writing the image
        """
        command = self.__prepare()
        command.extend(
            [
                f"stm32lx write_image{' erase ' if erase else ' '}{load_image}",
                "-c",
                "reset",
                "-c",
                "run",
                "-c",
                "shutdown",
            ]
        )
        self.run_command(command)

    def read(self, address, size, dir, readout):
        """
        Args:
            readout: Path to the readout file.
        """
        props = {"datetime": datetime.now()}
        if self.target:
            props["target"] = Path(self.target).stem
        if self.interface:
            props["interface"] = Path(self.interface).stem
        if self.serial:
            props["serial"] = self.serial

        readout_dir = Path(dir).resolve()
        readout_dir.mkdir(parents=True, exist_ok=True)

        readout_file = readout_dir / Path(readout.format(**props))
        command = self.__prepare()
        command.extend(
            ["-c", f"dump_image {readout_file} {address} {size}", "-c", "shutdown"]
        )
        self.run_command(command)

    def write(self, address, image_path):
        """Write an image to SRAM
        Args:
            address: Start address of the SRAM
            image_path: Path to the file to load in SRAM
        """
        command = self.__prepare()
        command.extend(["-c", f"load_image {image_path} {address}", "-c", "shutdown"])
        self.run_command(command)


if __name__ == "__main__":

    class CustomFormatter(
        argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter
    ):
        pass

    epilog_all = """
Indicate the directory where openocd will look for the TCL scripts using the `--openocd-path`. Additionally, a custom openocd binary can be specified using `--openocd-path`.
$ %(prog)s --openocd-path /path/to/custom/openocd --openocd-scripts /opt/OpenOCD/tcl

The interface and target are specified using the `--interface` and `--target` flags respectively
$ %(prog)s --interface="interface/stlink.cfg" --target="board/st_nucleo_l1.cfg"

If multiple devices are connected, the `--serial` flag can be used to specify the device. The serial can be obtained from running `lsusb -v` and looking for idSerial.
$ %(prog)s --interface="interface/stlink.cfg" --target="board/st_nucleo_l1.cfg"" --serial="066CFF383834434153328"

Additional configuration can be provided directly in a TCL script for openocd. This configuration assumes that the interface and target are provided.

# Example of TCL configuration
source [find interface/stlink.cfg]
source [find board/st_nucleo_l1.cfg]
adapter speed 4000
reset_config srst_only srst_nogate connect_assert_srst

$ %(prog)s --config /path/to/config.cfg

To run in verbose mode and see the command being executed and the output of openocd, pass the `-v` or `--verbose` flag.
"""

    parser = argparse.ArgumentParser(formatter_class=CustomFormatter, epilog=epilog_all)
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Print the output of the commands"
    )
    parser.add_argument(
        "--openocd-scripts", help="Path to the OpenOCD TCL scripts", required=False
    )
    parser.add_argument(
        "--openocd-path",
        help="Path to the OpenOCD binary. Defaults to the one in $PATH",
        required=False,
    )
    parser.add_argument(
        "-i",
        "--interface",
        help="The debug probe interface config file.",
        required=False,
    )
    parser.add_argument(
        "-t", "--target", help="The target device family", required=False
    )
    parser.add_argument("-c", "--config", help="Path to a TCL script", required=False)
    parser.add_argument(
        "-s", "--serial", help="Serial number of the device", required=False
    )

    subparsers = parser.add_subparsers(dest="command", description="Available commands")

    epilog_flash = """
To erase the FLASH of the device, pass the `--erase` flag
$ openocd_stm32.pys --config config.cfg flash --erase --load image.bin

To load an image into FLASH, provide the path to the image using the `--load` flag
$ openocd_stm32.py --config config.cfg flash --load image.elf

If the `--erase` flag is passed alongside the `--load` flag, force a mass erase of the unused FLASH
$ openocd_stm32.py --config config.cfg flash --erase --load image.elf
"""
    parser_flash = subparsers.add_parser(
        "flash",
        formatter_class=CustomFormatter,
        help="Erase the content of flash memory",
        epilog=epilog_flash,
    )
    parser_flash.add_argument(
        "--erase", help="Mass erase the flash", action="store_true"
    )
    parser_flash.add_argument("--load", help="Load an elf executable into flash")

    epilog_read = """
To read the SRAM contents, provide the starting address of the SRAM, and the number of bytes to read. You can get this information from the respective datasheet

$ openocd_stm32.py --config config.cfg read --address 0x20000000 --size 0x14000

The directory to where to store the readouts can be specified using the `--dir` flag. Moreover, the name of the readout file can be specified using the `--readout` flag. The name is formatted using the Python function `format` and the variables `target`, `interface`, `serial` and `datetime` are available.

$ openocd_stm32.py --config config.cfg read --address 0x20000000 --size 0x14000 --dir /path/to/readouts --readout '{target}-{serial}-{datetime:%H-%M}.bin'
"""
    parser_read = subparsers.add_parser(
        "read",
        help="Read the contents of the STM32 SRAM",
        formatter_class=CustomFormatter,
        epilog=epilog_read,
    )
    parser_read.add_argument(
        "--address",
        help="SRAM start address",
        default="0x20000000",
        required=True,
    )
    parser_read.add_argument(
        "--size",
        help="Number of bytes to read",
        required=True,
    )
    parser_read.add_argument(
        "--dir",
        type=str,
        help="Directory to store the readouts",
        default=".",
        required=False,
    )
    parser_read.add_argument(
        "--readout",
        type=str,
        help="Path to readout file",
        default="{target}--{datetime:%Y-%m-%d--%H-%M-%S}.bin",
        required=False,
    )

    epilog_write = """
To write custom data to the SRAM, pass the start address of SRAM to write and the path to the image to write. The number of bytes to write is computed automatically.
$ openocd_stm32.py --config config.cfg write --address 0x20000000 --image image.bin
"""
    parser_write = subparsers.add_parser(
        "write",
        help="Write data to the STM32 SRAM",
        formatter_class=CustomFormatter,
        epilog=epilog_write,
    )
    parser_write.add_argument(
        "--address",
        help="SRAM start address",
        default="0x20000000",
        required=True,
    )
    parser_write.add_argument("--image", help="Path to image file to write to SRAM")
    args = parser.parse_args()

    driver = Driver(
        target=args.target,
        interface=args.interface,
        openocd_bin=args.openocd_path,
        openocd_scripts=args.openocd_scripts,
        config=args.config,
        serial=args.serial,
        verbose=args.verbose,
    )

    if args.command == "read":
        code = driver.read(args.address, args.size, args.dir, args.readout)
        sys.exit(code)

    if args.command == "flash":
        if args.load:
            code = driver.flash_load(args.load_image, erase=args.erase)
        else:
            code = driver.flash_erase()
        sys.exit(code)

    if args.command == "write":
        code = driver.write(args.address, args.image)
        sys.exit(code)
