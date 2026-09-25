# Zynq UltraScale+ PS, used only for pl_clk0 (100 MHz) and pl_resetn0.
# When the bitstream is loaded from Linux (xmutil/fpga-manager) the PS is already configured,
# and the actual pl_clk0 rate comes from the device tree overlay.
create_bd_design "block_design"
set ps [create_bd_cell -type ip -vlnv xilinx.com:ip:zynq_ultra_ps_e ps]
set_property -dict {
  CONFIG.PSU__USE__M_AXI_GP0 0
  CONFIG.PSU__USE__M_AXI_GP1 0
  CONFIG.PSU__USE__M_AXI_GP2 0
  CONFIG.PSU__FPGA_PL0_ENABLE 1
  CONFIG.PSU__CRL_APB__PL0_REF_CTRL__FREQMHZ 100
} $ps
make_bd_pins_external -name pl_clk0 [get_bd_pins ps/pl_clk0]
make_bd_pins_external -name pl_resetn0 [get_bd_pins ps/pl_resetn0]
validate_bd_design
save_bd_design
