# hackathon

VHDL project for the Kria KV260, built with [tsfpga](https://tsfpga.com) and simulated with
[VUnit](https://vunit.github.io).

## Setup

```sh
git clone --recurse-submodules https://github.com/ru551n/hackathon.git
cd hackathon
uv venv
uv pip install -r requirements.txt
source .venv/bin/activate
```

Already cloned without submodules? `git submodule update --init --recursive`.
The recursive part matters: Open Logic has its own `en_cl_fix` submodule.

Tools:

- Vivado 2025.2 on `PATH` (`source <install>/Vivado/2025.2/settings64.sh`), with the Zynq
  UltraScale+ device family installed.
- A simulator: GHDL, NVC or Questa (see [Which simulator](#which-simulator)). VUnit picks the
  first one it finds, so set it explicitly: `export VUNIT_SIMULATOR=ghdl` (or `nvc`, `modelsim`).

## Simulate

```sh
python simulate.py                 # run all testbenches
python simulate.py "kv260.*"       # run matching testbenches
python simulate.py --compile       # compile only
python simulate.py --list          # list testbenches
python simulate.py --wave ...      # dump waveforms
python simulate.py --vivado-skip   # no Vivado available
```

The first run compiles the Vivado simulation libraries (unisim) with Vivado, which takes a while.
The result is cached in `simulate/`.

hdl-modules is compiled but its own testbenches are not run.

### Which simulator

| Design contains | Simulator |
|---|---|
| Only VHDL | GHDL or NVC |
| Verilog/SystemVerilog, VHDL testbench | NVC, if the code stays inside its subset; otherwise Questa |
| `interface`, `'0`, `unique`/`priority case`, or a SystemVerilog testbench | Questa |

- GHDL does not simulate Verilog or SystemVerilog at all.
- NVC takes Verilog/SystemVerilog through VUnit only because our VUnit branch
  (`ru551n/vunit@feature/waves`) carries upstream PR #1203. VUnit's own SystemVerilog test
  runner does not parse in NVC, so testbenches stay VHDL.
- Instantiate a Verilog/SystemVerilog module from VHDL with a component declaration
  (`dut : component name`). NVC rejects `entity work.name` for a Verilog module.

Questa (Altera Starter Edition, `~/altera_pro/26.1/questa_fse`):

```sh
export SALT_LICENSE_SERVER=<path to your license .dat>   # vsim 2025.3 reads this variable
VUNIT_SIMULATOR=modelsim python simulate.py --vivado-skip
```

Without `SALT_LICENSE_SERVER` every test fails in a fraction of a second with an empty log.
`--vivado-skip` is required: Vivado's `compile_simlib` refuses this Questa edition, so unisim is
not available and `hard_fifo` is left out. Check the Starter Edition's license terms before using
it for an AMD design.

## Build

```sh
python build.py --list                    # list build projects
python build.py kv260                     # create + build the KV260 bitstream
python build.py --netlist-builds --list   # hdl-modules' netlist (resource check) builds
```

Output lands in `build/<project>/`: `kv260.bit` and `kv260.xsa`.
A build of the current top level takes about 2.5 minutes.

## Lint and format

[speja](https://github.com/ru551n/speja) (installed by `requirements.txt`) with the house style in
`speja.yaml`: tsfpga/hdl-modules conventions, and no end statement repeats a name or label.

```sh
speja <files> --fix -c speja.yaml                            # format
speja --recursive modules --check style,lint -c speja.yaml   # check everything
```

Put files and `--recursive` before `-c`: `-c` takes several values. To exempt a deliberate
exception, wrap it in `-- vsg_off <rule>` / `-- vsg_on <rule>` with a comment saying why.

## Layout

```
modules/<name>/           our modules (tsfpga layout)
  module_<name>.py        build projects, VUnit test configs
  src/                    synthesizable VHDL
  test/                   testbenches (tb_*.vhd)
  tcl/                    constraints, block design
hdl-modules/              submodule, tsfpga modules (FIFOs, AXI, resync, ...)
open-logic/               submodule, Open Logic (library olo)
common.py                 module collection shared by simulate.py and build.py
```

A new module is a folder under `modules/`. Its library name is the folder name.

## Libraries

- **hdl-modules**: each module is its own library, e.g. `library fifo;`, `library axi_lite;`.
  Docs: <https://hdl-modules.com>.
- **Open Logic**: everything is in `library olo;`, e.g. `entity olo.olo_base_fifo_sync`.
  Docs: <https://github.com/open-logic/open-logic/blob/main/doc/EntityList.md>.

## KV260

| Item     | Value                                                                  |
|----------|------------------------------------------------------------------------|
| Part     | `xck26-sfvc784-2LV-c`                                                  |
| PL clock | `pl_clk0` from the PS, 100 MHz                                         |
| PL reset | `pl_resetn0` from the PS, active low                                   |
| PMOD J2  | pins H12, E10, D10, C11, B10, E12, D11, B11 (`pmod[0..7]`), LVCMOS33   |

The PS block design is `modules/kv260/tcl/block_design.tcl`. When the bitstream is loaded from
Linux, the PS is already running and the real `pl_clk0` rate comes from the device tree overlay.

The board sits in a server room: there is no physical access. Debug via registers readable from
Linux, or the ILA if JTAG is reachable through `hw_server`.
