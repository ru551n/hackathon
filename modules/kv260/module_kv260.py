"""Kria KV260 top level."""

from pathlib import Path

from tsfpga.constraint import Constraint
from tsfpga.module import BaseModule
from tsfpga.vivado.project import VivadoProject

from common import get_all_modules


class Module(BaseModule):
    def get_build_projects(self):
        tcl = self.path / "tcl"
        return [
            VivadoProject(
                name="kv260",
                modules=get_all_modules(),
                part="xck26-sfvc784-2LV-c",
                top="kv260_top",
                tcl_sources=[tcl / "block_design.tcl"],
                constraints=[Constraint(tcl / "kv260_pinning.tcl")],
                defined_at=Path(__file__),
            )
        ]
