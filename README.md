# Practical Activities on PUFs and TRNGs

Resources for the SERICS Autumn School on Hardware Security, in Turin, Italy

This repository contains the following files:

```text
├── data                       # Directory to store readouts
├── docs                       # Presentation resources
├── 00-install_st_openocd.sh   # Script to install openocd
├── 01-collect_readouts.sh     # Script to mass erase and obtain a readout
├── 02-get_nist.sh             # Script to download the NIST suite
├── openocd_stm32.py           # Python wrapper around openocd 
├── stm31l152re.template.cfg   # Template configuration for openocd
└── README.md
```

## Using the openocd wrapper

Openocd needs to have access to the configuration scripts for the STM32 microcontrollers.

The script `00-install_st_openocd.sh` will download the ST version of openocd alongside the configuration scripts, and build the `openocd` from source if it's not already in the system.

You can modify the script to download the repository to another directory, but you will need to pass the absolute path of the `tcl` directory to the wrapper

To mass erase the flash (Should be done at least once)
```bash
python3 openocd_stm32.py --openocd-scripts "/path/to/openocd/tcl" \
    --interface "interface/stlink.cfg" --target="board/stm32ldiscovery.cfg" \
    flash --erase
```

To obtain a readout. Size should be in bytes. 32kB for these boards
```bash
python3 openocd_stm32.py --openocd-scripts "/path/to/openocd/tcl" \
    --interface "interface/stlink.cfg" --target="board/stm32ldiscovery.cfg" \
    read --address 0x20000000 --size 0x8000 --dir "${READOUTS_DIR}"
```

## Running NIST test suite

The script `02-get_nist.sh` will download the C source code of the NIST SP 800-22 suite and build it from source.

It will also create a `config.txt` that serves as the input for the `assess` program, to avoid having to input the parameters one by one

```text
0                      # Test input file
/path/to/bitstream.txt # Path to input file
1                      # Run all tests
0                      # Run the tests on a bitstream
10                     # Number of bitstreams to test
0                      # 0 for ASCII and 1 for binary file
```

Then you need to provide to assess the length of each bitstream (in bits) alongside with the configuration (otherwise you'll need to input the parameters by hand)

```bash
./assess 10000 < config.txt
```

The final results are written to a text file

```bash
cat experiments/AlgorithmTesting/finalAnalysisReport.txt
```

## Presentation

The presentation is created using [Quarto](https://quarto.org). To compile the presentation into revealjs format:

```bash
$ quarto render docs/index.qmd
```

The resulting presentation will be created in `docs/index.html`. When opening the presentation in the browser, you can use the tools provided by revealjs to print the presentation to a PDF.
