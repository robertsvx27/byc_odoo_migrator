#!/usr/bin/env python3
import argparse
import os
import pathlib
import re
import sys
from pprint import pprint

import argcomplete
from colorama import Fore, Style

from xomg_migration.migrations.engine.migration_engine import OdooMigrationEngine
from xomg_migration.migrations.engine.migration_rule import FileType
from xomg_migration.migrations.log import setup_logger
from xomg_migration.migrations.transformers import tools, constants
from xomg_migration.migrations.transformers.exception import ConfigException


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
        "-r",
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
        "-ll",
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        dest="log_level",
        default="INFO",
        type=str,
    )
    main_parser.add_argument(
        "-ls",
        "--log-light",
        action="store_true",
        dest="log_light",
        default=True,
        help="",
    )
    main_parser.add_argument(
        "-lp",
        "--log-path",
        dest="log_path",
        default=False,
        type=str,
    )
    main_parser.add_argument(
        "-xm",
        "--ex-modules",
        dest="excluded_modules",
        type=str,
        help="Source Modules excluded to  migrate."
             " If not set, all the modules present in the directory will be"
             " migrated.",
    )
    main_parser.add_argument(
        "-xd",
        "--ex-dirs",
        dest="excluded_dirs",
        type=str,
        help="Excluded directories for search"
    )
    main_parser.add_argument('-e','--types', type=str, dest='file_types',
                        default='.py', help='File types to process')
    main_parser.add_argument('-p','--patterns', dest='file_patterns',type=str, help='File patterns to include (e.g., models/*.py)')
    main_parser.add_argument('-v','--verbose',  action='store_true', help='Verbose output')
    return main_parser

def main(args=False):
    parser = get_parser()
    argcomplete.autocomplete(parser, always_complete_options=False)
    if args:
        args = parser.parse_args(args)
    else:
        args = parser.parse_args()
        # Set log level
    dry_run = args.dry_run

    if not dry_run:
        print(f"{Fore.RED}{Style.BRIGHT}")
        print("⚠️  WARNING: LIVE MODE - Changes will be applied!")
        print("Press Ctrl+C to cancel or Enter to continue...")
        try:
            input()
        except KeyboardInterrupt:
            print("\nCancelled.")
            print(f"{Fore.RESET}{Style.NORMAL}")
            sys.exit(0)
        finally:
            print(f"{Fore.RESET}{Style.NORMAL}")

    setup_logger(args.log_level, args.log_path)

    try:

        mod_names = (
                args.modules
                and {x.strip() for x in args.modules.split(",") if x.strip()}
                or {}
        )
        f_patterns = (
                args.file_patterns
                and {x.strip() for x in args.file_patterns.split(",") if x.strip()}
                or {}
        )
        f_types = (
                args.file_types
                and {x.strip() for x in args.file_types.split(",") if x.strip()}
                or {}
        )
        excluded_modules = (
                args.excluded_modules
                and {x.strip() for x in args.excluded_modules.split(",") if x.strip()}
                or {}
        )
        exc_dirs = (
                args.excluded_dirs
                and {x.strip() for x in args.excluded_dirs.split(",") if x.strip()}
                or {}
        )
        modules_name = mod_names
        if not modules_name:
            modules_name = {}
        ex_dirs = set(constants._DEFAULT_EXCLUDED_DIRS)
        excluded_dirs = ex_dirs
        if exc_dirs:
            excluded_dirs.update(exc_dirs)
        fx_patterns = {}
        file_patterns = {}
        if f_patterns:
            for f in f_patterns:
                if f in constants._ALLOWED_EXTENSIONS:
                    file_patterns.update(f)
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
        print_types = {}
        # Mapear tipos de archivo
        if f_types:
            file_types = [FileType(ft) for ft in f_types]
        else:
            file_types = set(constants._ALLOWED_EXTENSIONS)

        modules.update(tools.get_modules_info(str(_directory_path), depth=5,
                                              modules_name=modules_name,
                                              file_types=file_types,
                                              file_patterns=file_patterns,
                                              exc_dirs=excluded_dirs,
                                              exc_modules=excluded_modules))
        if not modules:
            raise ConfigException("No modules found to migrate. Exiting.")
        print(f"{Fore.CYAN}Starting migration from {args.from_version} to {args.to_version}")
        print(f"{Fore.CYAN}Root Path: {_directory_path}")
        print(f"{Fore.CYAN}Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        print(f"{Fore.CYAN}File types: {', '.join([f.value for f in file_types])}")
        engine = OdooMigrationEngine(base_path=str(_directory_path),config_file=config_file,
                                     from_version=from_version,
                                     target_version=to_version, modules_path=modules,
                                     file_types=file_types,
                                     file_patterns=file_patterns, excluded_dirs=excluded_dirs,
                                     dry_run=dry_run)
        engine.run()
        # reports = []
        # for module, values in modules.items():
        #     report = engine.migrate_module(module_path=values['abs_path'], from_version=from_version, to_version=to_version)
        #     if log_enable == 'light' and report.status != 'empty':
        #         reports.append(report.to_light_dict())
        #     elif log_enable == 'full' and report.status != 'empty':
        #         reports.append(report.to_dict())
        #
        # pprint(reports,width=280,indent=2,sort_dicts=True)
        print('finish')
        print(f"{Fore.RESET}{Style.NORMAL}")
    except KeyboardInterrupt:
        print(f"{Fore.RESET}{Style.NORMAL}")

if __name__ == "__main__":
    main(sys.argv[1:])