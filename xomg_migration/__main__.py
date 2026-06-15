#!/usr/bin/env python3
import argparse
import os
import pathlib
import sys
from pprint import pprint

import argcomplete
from colorama import Fore

from migrations.engine.rule_loader import FileType
from .migrations.engine.migration_engine import OdooMigrationEngine
from .migrations.transformers import tools, constants
from .migrations.transformers.exception import ConfigException


def get_parser():
    main_parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    main_parser.add_argument(
        "-d",
        "--dir",
        dest="directory",
        default="./",
        type=str,
        help="Target Modules directory. Set here a folder path"
        " that contains Odoo modules you want to migrate from a version"
        " to another.",
    )
    main_parser.add_argument(
        "-p",
        "--dry-run",
        action="store_true",
        dest="dry_run",
        default=False,
        help="",
    )
    main_parser.add_argument(
        "-c",
        "--config",
        dest="config_file",
        default="./migration_config.yaml",
        type=str)
    main_parser.add_argument(
        "-i",
        "--from",
        choices=constants.SUPPORTED_VERSIONS,
        dest="from_version",
        required=True,
        type=str,
    )

    main_parser.add_argument(
        "-t",
        "--to",
        dest="to_version",
        type=str,
        choices=constants.SUPPORTED_VERSIONS,
        default=tools.get_latest_version_code(),
        help="")

    main_parser.add_argument(
        "-m",
        "--modules",
        dest="modules",
        type=str,
        help="Target Modules to migrate."
             " If not set, all the modules present in the directory will be"
             " migrated.",
    )
    main_parser.add_argument(
        "-l",
        "--log",
        action="store_true",
        dest="log_full",
        default=False,
        help="",
    )
    main_parser.add_argument(
        "-ls",
        "--log-light",
        action="store_true",
        dest="log_light",
        default=True,
        help="",
    )
    main_parser.add_argument('--types', nargs='+',
                             choices=['.py', '.xml', '_view.xml', '_security.xml', '_data.xml'],
                        default=['.py', '.xml'], help='File types to process')
    main_parser.add_argument('--patterns', nargs='+', help='File patterns to include (e.g., models/*.py)')
    main_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    return main_parser

def main(args=False):
    parser = get_parser()
    argcomplete.autocomplete(parser, always_complete_options=False)
    if args:
        args = parser.parse_args(args)
    else:
        args = parser.parse_args()
    try:

        module_names = (
                args.modules
                and [x.strip() for x in args.modules.split(",") if x.strip()]
                or []
        )
        if not module_names:
            module_names = []
        config_file = args.config_file
        from_version = args.from_version
        to_version = args.to_version
        relative_directory_path = args.directory
        dry_run = args.dry_run
        log_enable = 'disable'
        if args.log_full:
            log_enable = 'full'
        elif args.log_light:
            log_enable = 'light'

        if not os.path.exists(relative_directory_path):
            raise ConfigException(
                "Unable to find directory: %s" % relative_directory_path
            )
        root_path = pathlib.Path(relative_directory_path)
        _directory_path = pathlib.Path(root_path.resolve(strict=True))
        modules = {}
        # Mapear tipos de archivo
        file_types = [FileType(ft) for ft in args.types]
        modules.update(tools.get_modules_info(str(_directory_path), depth=5, modules_name=module_names))
        if not modules:
            raise ConfigException("No modules found to migrate. Exiting.")
        print(f"{Fore.CYAN}Starting migration from {args.from_version} to {args.to_version}")
        print(f"{Fore.CYAN}Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        print(f"{Fore.CYAN}File types: {', '.join(args.types)}")
        engine = OdooMigrationEngine(config_file=config_file, target_version=to_version, dry_run=dry_run)
        reports = []
        for module, values in modules.items():
            report = engine.migrate_module(module_path=values['abs_path'], from_version=from_version, to_version=to_version)
            if log_enable == 'light' and report.status != 'empty':
                reports.append(report.to_light_dict())
            elif log_enable == 'full' and report.status != 'empty':
                reports.append(report.to_dict())

        pprint(reports,width=280,indent=2,sort_dicts=True)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main(sys.argv[1:])