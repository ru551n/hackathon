"""Simulate all modules collected from the git submodules."""

import os

from tsfpga.examples.simulation_utils import (
    SimulationProject,
    create_vhdl_ls_configuration,
    get_arguments_cli,
)
from tsfpga.module_list import ModuleList

from common import REPO_ROOT, get_all_modules


def main():
    args = get_arguments_cli(default_output_path=REPO_ROOT / "simulate").parse_args()

    modules = get_all_modules()
    simulation_project = SimulationProject(args=args)
    simulation_project.vunit_proj.add_package("vunit-python-bridge", allow_setup=True)

    # Generate before modules are added to VUnit, to avoid duplicate files.
    create_vhdl_ls_configuration(
        output_path=REPO_ROOT, modules=modules, vunit_proj=simulation_project.vunit_proj
    )

    # hdl-modules is a dependency: compile it, but do not run its testbenches.
    # olo must stay in `modules`, tsfpga only calls setup_vunit (its compile flags) for those.
    tested, untested = ModuleList(), ModuleList()
    for module in modules:
        (untested if module.path.is_relative_to(REPO_ROOT / "hdl-modules") else tested).append(module)
    simulation_project.add_modules(modules=tested, modules_no_test=untested)
    # hdl-modules' hard_fifo wraps Xilinx primitives, so unisim must be available.
    # add_vivado_simlib() adds unisim, then sets a sim option on every testbench, which raises
    # when there are none (hdl-modules tests are excluded). The libraries are in by then.
    try:
        simulation_project.add_vivado_simlib()
    except ValueError as error:
        if "No test benches found" not in str(error):
            raise

    # Some test names are long enough to blow the file name limit.
    os.environ["VUNIT_SHORT_TEST_OUTPUT_PATHS"] = "true"
    simulation_project.vunit_proj.main()


if __name__ == "__main__":
    main()
