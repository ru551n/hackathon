"""Simulate all modules collected from the git submodules."""

import os

from tsfpga.examples.simulation_utils import (
    SimulationProject,
    create_vhdl_ls_configuration,
    get_arguments_cli,
)
from tsfpga.module import get_modules

from build import REPO_ROOT, submodule_module_folders


def main():
    args = get_arguments_cli(default_output_path=REPO_ROOT / "simulate").parse_args()

    modules = get_modules(modules_folders=submodule_module_folders())
    simulation_project = SimulationProject(args=args)

    # Generate before modules are added to VUnit, to avoid duplicate files.
    create_vhdl_ls_configuration(
        output_path=REPO_ROOT, modules=modules, vunit_proj=simulation_project.vunit_proj
    )

    simulation_project.add_modules(modules=modules)
    # hdl-modules' hard_fifo wraps Xilinx primitives, so unisim must be available.
    simulation_project.add_vivado_simlib()

    # Some test names are long enough to blow the file name limit.
    os.environ["VUNIT_SHORT_TEST_OUTPUT_PATHS"] = "true"
    simulation_project.vunit_proj.main()


if __name__ == "__main__":
    main()
