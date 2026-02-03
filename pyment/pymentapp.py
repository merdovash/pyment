#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import glob
import os
import fnmatch
import warnings
from dataclasses import dataclass, field, asdict
from typing import Literal

from argparse_dataclass import ArgumentParser

from pyment import PyComment
from pyment import (
    __version__,
    __copyright__,
    __author__,
    __licence__,
)
from pyment.configs import CommentBuilderConfig, ReadConfig, ActionConfig
from pyment.utils import from_dict

MAX_DEPTH_RECUR = 50
''' The maximum depth to reach while recursively exploring sub folders'''



@dataclass
class PymentOptions:
    """Command-line options for the Pyment application."""

    path: list[str] = field(
        default_factory=list,
        metadata={
            "args": ["path"],
            "nargs": "*",
            "type": str,
            "help": (
                "python file(s) or folder(s) containing python files to proceed "
                "(explore also sub-folders). Use '-' to read from stdin and write "
                "to stdout. Can accept multiple files/folders."
            ),
        },
    )
    input: str = field(
        default="auto",
        metadata={
            "args": ["-i", "--input"],
            "kwargs": {
                "metavar": "style",
                "help": (
                    'Input docstring style in ["javadoc", "reST", "numpydoc", '
                    '"google", "auto"] (default autodetected)'
                ),
            },
        },
    )
    output: Literal["javadoc", "reST", "numpydoc", "google"] = field(
        default="reST",
        metadata={
            "args": ["-o", "--output"],
            "kwargs": {
                "metavar": "style",
                "help": (
                    'Output docstring style in ["javadoc", "reST", "numpydoc", "google"] (default "reST")'
                ),
            },
        },
    )
    quotes: str = field(
        default='"""',
        metadata={
            "args": ["-q", "--quotes"],
            "kwargs": {
                "metavar": "quotes",
                "help": (
                    "Type of docstring delimiter quotes: ''' or \"\"\" (default \"\"\"). "
                    "Note that you may escape the characters using \\ like \\'\\'\\', "
                    "or surround it with the opposite quotes like \"'''\""
                ),
            },
        },
    )
    first_line: bool = field(
        default=True,
        metadata={
            "args": ["-f", "--first-line"],
            "kwargs": {
                "metavar": "status",
                "help": (
                    "Does the comment starts on the first line after the quotes "
                    '(default "True")'
                ),
            },
        },
    )
    convert: bool = field(
        default=False,
        metadata={
            "args": ["-t", "--convert"],
            "kwargs": {
                "action": "store_true",
                "help": (
                    "Existing docstrings will be converted but won't create missing ones"
                ),
            },
        },
    )
    config_file: str = field(
        default="",
        metadata={
            "args": ["-c", "--config-file"],
            "kwargs": {
                "metavar": "config",
                "help": (
                    "Get a Pyment configuration from a file. Note that the config "
                    "values will overload the command line ones."
                ),
            },
        },
    )
    init2class: bool = field(
        default=False,
        metadata={
            "args": ["-d", "--init2class"],
            "kwargs": {
                "action": "store_true",
                "help": "If no docstring to class, then move the __init__ one",
            },
        },
    )
    ignore_private: str = field(
        default="True",
        metadata={
            "args": ["-p", "--ignore-private"],
            "kwargs": {
                "metavar": "status",
                "help": (
                    "[DEPRECATED] Don't proceed the private methods/functions starting "
                    'with __ (two underscores) (default "True"). Use --method-scope '
                    "instead. This option will be removed in a future version."
                ),
            },
        },
    )
    overwrite: bool = field(
        default=False,
        metadata={
            "args": ["-w", "--write"],
            "kwargs": {
                "action": "store_true",
                "help": (
                    "Don't write patches. Overwrite files instead. If used with path "
                    "- won't overwrite but write to stdout the new content instead of "
                    "a patch/."
                ),
            },
        },
    )
    spaces: int = field(
        default=4,
        metadata={
            "args": ["-s", "--spaces"],
            "kwargs": {
                "metavar": "spaces",
                "type": int,
                "help": (
                    "The default number of spaces to use for indenting on output. "
                    "Default is 4."
                ),
            },
        },
    )
    skip_empty: bool = field(
        default=False,
        metadata={
            "args": ["-e", "--skip-empty"],
            "kwargs": {
                "action": "store_true",
                "help": (
                    "Don't write params, returns, or raises sections if they are empty."
                ),
            },
        },
    )
    file_comment: bool = field(
        default=False,
        metadata={
            "args": ["--file-comment"],
            "kwargs": {
                "action": "store_true",
                "help": (
                    "Add a file comment with the file name at the beginning of the file."
                ),
            },
        },
    )
    extensions: str = field(
        default=None,
        metadata={
            "args": ["--extensions"],
            "kwargs": {
                "metavar": "extensions",
                "help": (
                    'Comma-separated list of file extensions to process (e.g., "py,js"). '
                    "Extensions can include or omit the leading dot."
                ),
            },
        },
    )
    encoding: str = field(
        default="utf-8",
        metadata={
            "args": ["--encoding"],
            "kwargs": {
                "metavar": "encoding",
                "help": (
                    'The encoding to use when reading and writing files '
                    '(default "utf-8"). Examples: utf-8, latin1, cp1252.'
                ),
            },
        },
    )
    exclude: str = field(
        default=None,
        metadata={
            "args": ["--exclude"],
            "kwargs": {
                "metavar": "patterns",
                "help": (
                    'Comma-separated list of filename patterns to exclude '
                    '(supports Unix shell-style wildcards, e.g., '
                    '"test_*.py,*_test.py"). Patterns match against the filename '
                    "or full path."
                ),
            },
        },
    )
    method_scope: str = field(
        default=None,
        metadata={
            "args": ["--method-scope"],
            "kwargs": {
                "metavar": "scope",
                "help": (
                    "Method scope to process: public, protected, or private. Can be "
                    "specified as a single value (e.g., --method-scope=public) or "
                    "comma-separated values (e.g., --method-scope=public,protected). "
                    "Default processes all methods."
                ),
            },
        },
    )
    show_default_value: bool = field(
        default=True,
        metadata={
            "args": ["--no-show-default-value"],
            "kwargs": {
                "action": "store_false",
                "help": (
                    "Do not include \"(Default value = ...)\" in parameter descriptions."
                ),
            },
        },
    )
    type_tags: bool = field(
        default=True,
        metadata={
            "args": ["--no-type-tags"],
            "kwargs": {
                "action": "store_false",
                "help": (
                    "Do not include :type and :rtype: fields in generated docstrings "
                    "(reST/javadoc styles)."
                ),
            },
        },
    )
    empty_lines_zero: bool = field(
        default=False,
        metadata={
            "args": ["--empty-lines-zero"],
            "kwargs": {
                "action": "store_true",
                "help": (
                    "Format completely empty lines in generated docstrings at zero "
                    "indentation level instead of the comment indentation level."
                ),
            },
        },
    )



def get_files_from_dir(path, recursive=True, depth=0, file_ext='.py', extensions=None, exclude=None):
    """Retrieve the list of files from a folder.

    @param path: file or directory where to search files
    @param recursive: if True will search also sub-directories
    @param depth: if explore recursively, the depth of sub directories to follow
    @param file_ext: the files extension to get. Default is '.py' (deprecated, use extensions instead)
    @param extensions: list of file extensions to filter by (e.g., ['.py', '.js']). If None, uses file_ext for backward compatibility.
    @param exclude: list of filename patterns to exclude (supports Unix shell-style wildcards, e.g., ['test_*.py', '*.test.py']). If None, no files are excluded.
    @return: the file list retrieved. if the input is a file then a one element list.

    """
    file_list = []
    if os.path.isfile(path) or path == '-':
        return [path]
    
    # Use extensions if provided, otherwise fall back to file_ext for backward compatibility
    if extensions is None:
        extensions = [file_ext]
    
    # Initialize exclude list if not provided
    if exclude is None:
        exclude = []
    
    if path[-1] != os.sep:
        path = path + os.sep
    for f in glob.glob(path + "*"):
        if os.path.isdir(f):
            if depth < MAX_DEPTH_RECUR:  # avoid infinite recursive loop
                file_list.extend(get_files_from_dir(f, recursive, depth + 1, file_ext, extensions, exclude))
            else:
                continue
        elif any(f.endswith(ext) for ext in extensions):
            # Check if file should be excluded
            filename = os.path.basename(f)
            should_exclude = False
            for pattern in exclude:
                if fnmatch.fnmatch(filename, pattern) or fnmatch.fnmatch(f, pattern):
                    should_exclude = True
                    break
            if not should_exclude:
                file_list.append(f)
    return file_list


def run(source, args: PymentOptions, files=[]):    
    # Track changes across all files
    files_changed = []
    has_changes = False

    comment_config = from_dict(CommentBuilderConfig, {
        **asdict(args),
        'method_scope': args.method_scope or (
        ['public', 'protected'] if args.ignore_private else ['public', 'protected', 'private']),
        'indent_empty_lines': not args.empty_lines_zero,
    })
    

    read_config = ReadConfig(
        encoding=args.encoding or 'utf-8',
    )

    action_config = ActionConfig(
        convert_only=args.convert,
    )

    for f in files:
        try:
            if os.path.isdir(source):
                path = source + os.sep + os.path.relpath(os.path.abspath(f), os.path.abspath(source))
                path = path[:-len(os.path.basename(f))]
            else:
                path = ''
            # Print filename before processing
            if f != '-':
                print(f)

            c = PyComment(
                f,
                comment_config=comment_config,
                read_config=read_config,
                action_config=action_config,
                input_style=args.input,
            )
            c.proceed()
            if comment_config.init2class:
                c.docs_init_to_class()

            # Compute before/after to detect changes (used for both overwrite and patch modes)
            list_from, list_to = c.compute_before_after()
            file_changed = list_from != list_to

            if args.overwrite:
                lines_to_write = list_to
            else:
                lines_to_write = c.get_patch_lines(path, path)

            # Debug: Print change status for this file
            if f != '-':
                if file_changed:
                    print(f"DEBUG: Changes detected in {f}", file=sys.stderr)
                    print(''.join(c.get_patch_lines(path, path)), file=sys.stderr)
                    files_changed.append(f)
                else:
                    print(f"DEBUG: No changes in {f}", file=sys.stderr)
            
            if file_changed:
                has_changes = True

            if f == '-':
                sys.stdout.writelines(lines_to_write)
            else:
                if args.overwrite:
                    if file_changed:
                        c.overwrite_source_file(lines_to_write)
                else:
                    if file_changed:
                        c.write_patch_file(os.path.basename(f) + ".patch", lines_to_write)
        except Exception as e:
            # Print error message and continue to next file
            if f != '-':
                print(f"\nError processing {f}: {str(e)}", file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)
            else:
                print(f"\nError processing stdin: {str(e)}", file=sys.stderr)
            continue
    
    # Debug: Print summary of changes
    print("DEBUG: Summary of changes:", file=sys.stderr)
    if files_changed:
        print(f"DEBUG:   {len(files_changed)} file(s) changed", file=sys.stderr)
    else:
        print("DEBUG:   No files changed", file=sys.stderr)
    
    return has_changes


def _main():   
    desc = "Pyment v{0} - {1} - {2} - {3}".format(
        __version__,
        __copyright__,
        __author__,
        __licence__,
    )

    parser = ArgumentParser(
        PymentOptions,
        description="Generates patches after (re)writing docstrings.",
    )
    # Keep explicit version flag behavior
    parser.add_argument("-v", "--version", action="version", version=desc)

    args = parser.parse_args()
    
    # Handle paths: support both single path (backward compatibility) and multiple paths (pre-commit hook)
    paths = args.path if args.path else []
    
    sys.stderr.write(f"DEBUG: Args received: {asdict(args)}\n")
    sys.stderr.flush()
    
    
    # If no paths provided, show error
    if not paths:
        parser.error("the following arguments are required: path")
    
    # Parse extensions if provided
    extensions = None
    if args.extensions:
        # Split by comma and normalize extensions (add leading dot if missing)
        ext_list = [ext.strip() for ext in args.extensions.split(',')]
        extensions = []
        for ext in ext_list:
            if ext and not ext.startswith('.'):
                extensions.append('.' + ext)
            elif ext:
                extensions.append(ext)

    # Parse exclude patterns if provided
    exclude = None
    if args.exclude:
        # Split by comma and strip whitespace
        exclude = [pattern.strip() for pattern in args.exclude.split(',') if pattern.strip()]

    # Convert deprecated ignore_private to method_scope
    tobool = lambda s: True if s.lower() == 'true' else False
    ignore_private = tobool(args.ignore_private)
    if ignore_private:
        warnings.warn(
            "The '--ignore-private' option is deprecated and will be removed in a future version. "
            "Use '--method-scope public --method-scope protected' instead.",
            DeprecationWarning,
            stacklevel=2
        )
    
    # Helper function to check if a file should be included
    def should_include_file(filepath):
        """Check if a file should be included based on extensions and exclude patterns."""
        # Check extensions if specified
        if extensions:
            if not any(filepath.endswith(ext) for ext in extensions):
                return False
        
        # Check exclude patterns if specified
        if exclude:
            filename = os.path.basename(filepath)
            for pattern in exclude:
                if fnmatch.fnmatch(filename, pattern) or fnmatch.fnmatch(filepath, pattern):
                    return False
        return True
    
    # Collect all files from all paths
    all_files = []
    for path in paths:
        # Handle stdin separately
        if path == '-':
            all_files.append(path)
        # If path is a file, add it directly after filtering
        elif os.path.isfile(path):
            if should_include_file(path):
                sys.stderr.write(f"DEBUG: File passed filters, adding to list: {path}\n")
                sys.stderr.flush()
                all_files.append(path)
            else:
                sys.stderr.write(f"DEBUG: Skipping file (filtered out): {path}\n")
                sys.stderr.flush()
        # If path is a directory, use get_files_from_dir (which already applies filters)
        elif os.path.isdir(path):
            sys.stderr.write(f"DEBUG: Found directory: {path}\n")
            sys.stderr.flush()
            files_from_path = get_files_from_dir(path, extensions=extensions, exclude=exclude)
            all_files.extend(files_from_path)
        else:
            # Path doesn't exist - skip it (pre-commit may pass non-existent files)
            sys.stderr.write(f"DEBUG: Skipping non-existent path: {path}\n")
            sys.stderr.flush()
    
    # Remove duplicates while preserving order
    seen = set()
    files = []
    for f in all_files:
        if f not in seen:
            seen.add(f)
            files.append(f)
    
    if files:
        for f in files:
            sys.stderr.write(f"DEBUG:   - {f}\n")
        sys.stderr.flush()
    else:
        sys.stderr.write("DEBUG:   (no files found)\n")
        sys.stderr.flush()
    
    if not files:
        # For pre-commit hooks, if no files match filters, exit successfully (no changes needed)
        # This is better than raising an error, as it allows the hook to pass when files are filtered out
        sys.stderr.write("DEBUG: No files to process after filtering - exiting with code 0\n")
        sys.stderr.flush()
        sys.exit(0)

    # Determine source for run() function - use first path if single, or empty string if multiple
    # The run() function uses source to determine relative paths for patches
    if len(paths) == 1:
        source = paths[0]
    else:
        # For multiple paths, we'll use empty string and let run() handle it
        source = ''

    has_changes = run(
        source,
        args,
        files 
    )
    
    # Exit with code 0 if no changes, non-zero if changes were made
    if has_changes:
        sys.stderr.write("DEBUG: Exiting with code 1 (changes were made)\n")
        sys.stderr.flush()
        sys.exit(1)
    else:
        sys.stderr.write("DEBUG: Exiting with code 0 (no changes)\n")
        sys.stderr.flush()
        sys.exit(0)


def main():
    try:
        _main()
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)


if __name__ == "__main__":
    main()