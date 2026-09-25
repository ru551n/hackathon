"""Module collection shared by build.py and simulate.py."""

import subprocess
import sys
from pathlib import Path

from tsfpga.constraint import Constraint
from tsfpga.module import BaseModule, get_modules

REPO_ROOT = Path(__file__).parent.resolve()


def submodule_module_folders():
    """Every submodule's `modules` folder, for those that have one."""
    paths = subprocess.check_output(
        ["git", "submodule", "--quiet", "foreach", "echo $sm_path"],
        cwd=REPO_ROOT,
        text=True,
    ).split()
    folders = []
    for path in paths:
        # Submodules ship helper packages (e.g. hdl_modules) that their module_*.py files import.
        sys.path.insert(0, str(REPO_ROOT / path))
        if (folder := REPO_ROOT / path / "modules").exists():
            folders.append(folder)
    return folders


class OloModule(BaseModule):
    """Open Logic, which is not laid out as tsfpga modules. Everything goes in library 'olo'."""

    @property
    def synthesis_folders(self):
        return [*(self.path / "src").glob("*/vhdl"), self.path / "3rdParty" / "en_cl_fix" / "hdl"]

    @property
    def test_folders(self):
        # ponytail: olo testbenches need the generic configs from olo's sim/run.py; not ported.
        return []

    def get_scoped_constraints(self, **kwargs):
        # One <entity>.tcl per entity; skip the *_constraints_amd.tcl loader scripts.
        return [
            Constraint(file, scoped_constraint=True, used_in_synthesis=False)
            for file in sorted((self.path / "src").glob("*/tcl/olo_*.tcl"))
            if not file.stem.endswith("_constraints_amd")
        ]

    def setup_vunit(self, vunit_proj, **kwargs):
        library = vunit_proj.library(self.library_name)
        library.add_compile_option("ghdl.a_flags", ["-frelaxed"])
        library.add_compile_option("nvc.a_flags", ["--relaxed"])


def get_olo_module():
    return OloModule(path=REPO_ROOT / "open-logic", library_name="olo")


def get_all_modules():
    """Our own modules, those from all submodules, plus Open Logic."""
    modules = get_modules(modules_folders=[REPO_ROOT / "modules", *submodule_module_folders()])
    modules.append(get_olo_module())
    return modules
