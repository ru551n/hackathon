"""Collect modules from all git submodules and build their FPGA projects."""

import argparse
import sys
from pathlib import Path

from tsfpga.build_project_list import BuildProjectList, get_build_projects

from common import REPO_ROOT, get_all_modules


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_filters", nargs="*", default=[], help="project names to build")
    parser.add_argument("--list", action="store_true", help="list projects and exit")
    parser.add_argument("--netlist-builds", action="store_true")
    parser.add_argument("--projects-path", type=Path, default=REPO_ROOT / "build")
    parser.add_argument("--num-parallel-builds", type=int, default=4)
    parser.add_argument("--num-threads-per-build", type=int, default=4)
    args = parser.parse_args()

    modules = get_all_modules()
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
