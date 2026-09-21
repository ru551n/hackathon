"""Collect modules from all git submodules and build their FPGA projects."""

import argparse
import subprocess
import sys
from pathlib import Path

from tsfpga.build_project_list import BuildProjectList, get_build_projects
from tsfpga.module import get_modules

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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_filters", nargs="*", default=[], help="project names to build")
    parser.add_argument("--list", action="store_true", help="list projects and exit")
    parser.add_argument("--netlist-builds", action="store_true")
    parser.add_argument("--projects-path", type=Path, default=REPO_ROOT / "build")
    parser.add_argument("--num-parallel-builds", type=int, default=4)
    parser.add_argument("--num-threads-per-build", type=int, default=4)
    args = parser.parse_args()

    modules = get_modules(modules_folders=submodule_module_folders())
    projects = BuildProjectList(
        projects=get_build_projects(
            modules=modules,
            project_filters=args.project_filters,
            include_netlist_not_full_builds=args.netlist_builds,
        )
    )
    print(f"{len(modules)} modules, {projects.get_short_str()}")

    if args.list:
        return 0

    return 0 if projects.build(
        projects_path=args.projects_path,
        num_parallel_builds=args.num_parallel_builds,
        num_threads_per_build=args.num_threads_per_build,
    ) else 1


if __name__ == "__main__":
    sys.exit(main())
