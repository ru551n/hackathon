# From https://github.com/Xilinx/Kria-PYNQ/blob/main/kv260/base/vivado/constraints/base.xdc
# PMOD J2, bank 45.
set_property -dict {"PACKAGE_PIN" "H12" "IOSTANDARD" "LVCMOS33"} [get_ports "pmod[0]"]
