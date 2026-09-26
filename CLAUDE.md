# CLAUDE.md

Setup, commands, layout and board facts are in `README.md`. Read it first.

## Flow

Work one module at a time through these steps. Do not skip ahead: an untested block in the
top level costs far more time on a remote board than the testbench would have.

1. **Specify.** Write down the module's ports, generics, latency and throughput before any
   RTL, as a header comment in the entity file. Use AXI-Stream (`valid`/`ready`/`data`) for
   data paths and AXI-Lite registers for control and status, so blocks compose.
2. **Reuse.** Check hdl-modules and Open Logic (`open-logic/doc/EntityList.md`) for the block
   or its parts (FIFOs, CDC, width converters, AXI, UART/SPI/I2C, fixed point). Only write what
   is missing.
3. **Test first.** Create `modules/<name>/test/tb_<entity>.vhd` with VUnit (`runner_cfg`
   generic, `test_runner_setup`, one `run("...")` per test case) from the spec. Check results
   against a reference: VUnit's AXI-Stream verification components for traffic, a Python
   model through `vunit-python-bridge` for data. Run it and see it fail:
   `python simulate.py "<name>.*"`.
4. **Implement** `modules/<name>/src/<entity>.vhd` until that testbench passes. Do not weaken
   a check to make it pass. Then lay out and lint source and testbench with speja:
   `speja <files> --fix -c speja.yaml`, then
   `speja <files> --check style,lint -c speja.yaml` must report 0 violations. Never lay out
   VHDL by hand, and never edit `speja.yaml` to silence a finding.
5. **Integrate.** Instantiate the module in `kv260_top` (or its own top) and extend the
   top-level testbench to cover the path through it.
6. **Build.** `python build.py kv260`. Read `build/kv260/output.txt` for resource use and the
   timing summary in `build/kv260/project/kv260.runs/impl_1/*timing_summary*.rpt`: WNS and
   WHS must be >= 0. Fix timing in the RTL (pipeline registers) before touching tool settings.
7. **Commit.** Small commits per module, after the module's tests pass. `git pull --rebase`
   before pushing; never push something that does not compile in `simulate.py --compile`.

## Components

Shorthand for step 2. `lib.entity`: hdl-modules has one library per module, Open Logic is all
`olo`. Read the entity's header before using it. Where both libraries have a block, either is
fine; stay consistent inside one module.

**CDC: hdl-modules only.** Every signal crossing clock domains goes through the blocks in the
CDC rows below; tsfpga applies their scoped constraints (`resync/` and `fifo/`
`scoped_constraints/`). Never use Open Logic's `olo_base_cc_*`, `olo_base_fifo_async` or
`olo_intf_sync`, and never write a synchronizer by hand. Only reset synchronization uses
`olo.olo_base_reset_gen`. Avoid `resync_rarely_valid`/`resync_rarely_valid_lutram`: their
header names a constraint file that does not exist in hdl-modules, so they build unconstrained.

| Need | Use |
|---|---|
| Sync FIFO | `fifo.fifo`, `olo.olo_base_fifo_sync`, `axi_stream.axi_stream_fifo` |
| Async FIFO (CDC) | `fifo.asynchronous_fifo`, `hard_fifo.asynchronous_hard_fifo` |
| Packet FIFO (drop/repeat) | `olo.olo_base_fifo_packet`, `common.clean_packet_dropper` |
| Primitive FIFO (FIFO36E2) | `hard_fifo.hard_fifo`, `hard_fifo.asynchronous_hard_fifo` |
| RAM | `olo.olo_base_ram_sp`, `olo.olo_base_ram_sdp`, `olo.olo_base_ram_tdp` |
| CDC single bit, input pin | `resync.resync_level`, `resync.resync_level_on_signal`, `resync.resync_sticky_level` |
| CDC pulse | `resync.resync_pulse` |
| CDC vector | `resync.resync_slv_level`, `resync.resync_slv_level_on_signal`, `resync.resync_twophase`, `resync.resync_twophase_handshake` |
| CDC counter | `resync.resync_counter` (Gray code) |
| CDC AXI / AXI-Lite | `axi.axi_read_cdc`/`axi_write_cdc`, `axi_lite.axi_lite_cdc` |
| Reset synchronizer | `olo.olo_base_reset_gen` (hdl-modules has none) |
| Pipeline/register slice | `common.handshake_pipeline`, `olo.olo_base_pl_stage`, `olo.olo_axi_pl_stage`, `axi.axi_read_pipeline`/`axi_write_pipeline`, `axi_lite.axi_lite_pipeline` |
| Stream split/merge/mux | `common.handshake_splitter`, `common.handshake_merger`, `common.handshake_mux`, `olo.olo_base_tdm_mux` |
| Arbiter | `olo.olo_base_arb_rr`, `olo.olo_base_arb_prio`, `olo.olo_base_arb_wrr` |
| Width conversion | `common.width_conversion`, `olo.olo_base_wconv_n2m`, `olo.olo_base_wconv_n2xn`, `olo.olo_base_wconv_xn2n` |
| Stream helpers | `common.assign_last`, `common.strobe_on_last`, `common.keep_remover`, `common.axi_stream_protocol_checker`, `olo.olo_base_flowctrl_handler`, `olo.olo_base_rate_limit` |
| Delay/latency match | `olo.olo_base_delay`, `olo.olo_base_delay_cfg`, `olo.olo_base_latency_comp` |
| Strobe/timer/counter | `olo.olo_base_strobe_gen`, `olo.olo_base_strobe_div`, `common.periodic_pulser`, `common.clock_counter`, `olo.olo_intf_clk_meas` |
| Debounce | `common.debounce`, `olo.olo_intf_debounce` |
| Registers (PS to PL) | `register_file.axi_lite_register_file` (+ hdl-registers `regs_<name>.toml`), `olo.olo_axi_lite_slave`, `register_file.interrupt_register` |
| AXI-Lite plumbing | `axi_lite.axi_to_axi_lite`, `axi_lite.axi_lite_mux`, `axi_lite.axi_lite_cdc`, `axi_lite.axi_to_axi_lite_vec` |
| AXI plumbing | `axi.axi_read_cdc`/`axi_write_cdc`, `axi.axi_*_fifo`, `axi.axi_simple_read_crossbar`/`write_crossbar`, `axi.axi_read_throttle`/`write_throttle` |
| AXI master to DDR | `olo.olo_axi_master_simple`, `olo.olo_axi_master_full` |
| DMA stream to DDR | `dma_axi_write_simple.dma_axi_write_simple_axi_lite`, `ring_buffer.ring_buffer_write_simple` |
| UART / SPI / I2C | `olo.olo_intf_uart`, `olo.olo_intf_spi_master`, `olo.olo_intf_spi_slave`, `olo.olo_intf_i2c_master` |
| CRC | `olo.olo_base_crc`, `olo.olo_base_crc_append`, `olo.olo_base_crc_check` |
| PRBS/LFSR | `olo.olo_base_prbs`, `lfsr.lfsr_fibonacci_single`, `lfsr.lfsr_fibonacci_multi` |
| Misc logic | `olo.olo_base_cam`, `olo.olo_base_dyn_sft` (barrel shift), `olo.olo_base_decode_firstbit`, `olo.olo_base_sample_hold`, `common.event_aggregator` |
| Integer math | `math.unsigned_divider`, `math.saturate_signed`, `math.truncate_round_signed`, `math.math_pkg` |
| Fixed-point arithmetic | `olo.olo_fix_add`/`sub`/`addsub`/`mult`/`madd`/`bin_div`/`abs`/`neg`/`compare`/`limit` |
| Fixed-point format | `olo.olo_fix_resize`, `olo.olo_fix_round`, `olo.olo_fix_saturate`, `olo.olo_fix_from_real`/`to_real` (constants, no pipeline); types and functions in `olo.olo_fix_pkg` (`en_cl_fix`, same rounding as its Python model) |
| DSP | `olo.olo_fix_mov_avg`, `olo.olo_fix_cic_dec_tdm`, `olo.olo_fix_fir_dec_ser_chpar`, `olo.olo_fix_cordic_rot`/`cordic_vect`, `olo.olo_fix_cplx_mult`/`cplx_addsub`, `olo.olo_fix_mix_r2c`/`mix_c2r` |
| Sine/cosine | `sine_generator.sine_generator`, `sine_generator.sine_lookup` |
| Utility packages | `common.types_pkg`, `common.common_pkg`, `common.addr_pkg`, `olo.olo_base_pkg_math`, `olo.olo_base_pkg_logic`, `olo.olo_base_pkg_array`, `axi.axi_pkg`, `axi_lite.axi_lite_pkg`, `axi_stream.axi_stream_pkg` |

Testbench only (never in `src/`):

- hdl-modules `bfm` library (`library bfm;`): `axi_stream_master`/`axi_stream_slave`,
  `axi_lite_master`, `axi_master`/`axi_slave` (with a memory model), `handshake_master`/
  `handshake_slave` (random stalls), `*_bfm_pkg` helpers.
- VUnit verification components (`library vunit_lib;`): AXI-Stream, AXI-Lite master, memory.
- `olo.olo_fix_sim_stimuli`, `olo.olo_fix_sim_checker`: apply fixed-point stimuli from a file
  and check DUT outputs against a file, e.g. written by the `en_cl_fix` Python model.

Ours: `kv260.kv260_top` (KV260 top level: PS clock/reset, PMOD blink).

## Debugging a failing test

- Rerun only the failing test: `python simulate.py "<lib>.<tb>.<test>" -v`.
- Read the failing check's message and the test's `output.txt` (VUnit prints its path)
  before looking at waveforms.
- For waveforms add `--wave` and open the file in GTKWave. Agents: never read a waveform file
  (`.vcd`, `.fst`, `.ghw`) as text; they can be hundreds of MB.
- Find the root cause before changing code. Change one thing, rerun the same test.

## Working rules

- Our code goes in `modules/<name>/` (tsfpga layout). Never edit `hdl-modules/` or
  `open-logic/`; they are pinned submodules.
- Set `VUNIT_SIMULATOR` explicitly; otherwise VUnit may pick Questa. Simulator split (details
  in README "Which simulator"):
  - only VHDL: `ghdl` or `nvc`;
  - Verilog/SystemVerilog design files under a VHDL testbench: `nvc`, unless the code uses
    `interface`, `'0` or `unique`/`priority case`, then `modelsim` (Questa);
  - never write testbenches in SystemVerilog: VUnit's SV runner does not work in NVC.
  Questa needs `SALT_LICENSE_SERVER` set and `--vivado-skip`; a test failing in 0.1 s with an
  empty log means the license variable is missing.
- Instantiate Verilog/SystemVerilog modules from VHDL through a component declaration
  (`dut : component name`), never `entity work.name`: NVC rejects that for Verilog.
- Keep a single testbench run under 5 minutes: shrink the scenario, not the checks.
- Run one Vivado build at a time.
- The board is remote with no physical access: make state observable through registers
  readable from Linux (version, counters, sticky error flags).

## Gotchas

- Open Logic uses `work.` internally, so all of it (and `en_cl_fix`) must be in the single
  library `olo`. `OloModule` in `common.py` handles this; it also adds the relaxed GHDL/NVC flags
  Open Logic needs.
- `OloModule.setup_vunit` only runs when olo is in `add_modules(modules=...)`, not in
  `modules_no_test`. Keep it there.
- `simulate.py` tolerates `add_vivado_simlib()` raising "No test benches found": it happens only
  while there are no testbenches of our own, after unisim is already added.
- Open Logic's per-entity `src/*/tcl/olo_*.tcl` are loaded as tsfpga scoped constraints. Do not
  source the `olo_*_constraints_amd.tcl` loader scripts as well.
- `kv260_top` is clocked by `pl_clk0` from the PS (`component block_design`, generated from
  `modules/kv260/tcl/block_design.tcl`).
- speja: put files and `--recursive` before `-c`, since `-c` takes several values and reads
  anything after it as a config. A deliberate exception gets `-- vsg_off <rule>` /
  `-- vsg_on <rule>` with a comment saying why, as around `block_design_inst` in `kv260_top`.
- End statements never repeat a name or label (`end entity;`, `end process;`,
  `end component;`). speja removes them; do not write them.
- `vhdl_ls.toml` is generated by `simulate.py` and gitignored. Do not commit it.
