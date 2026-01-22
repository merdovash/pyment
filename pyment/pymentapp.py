#!/usr/bin/python
# -*- coding: utf-8 -*-

import glob
import argparse
import os
import sys

from pyment import PyComment
from pyment import __version__, __copyright__, __author__, __licence__


MAX_DEPTH_RECUR = 50
''' The maximum depth to reach while recursively exploring sub folders'''


def get_files_from_dir(path, recursive=True, depth=0, file_ext='.py', extensions=None):
    """Retrieve the list of files from a folder.

    @param path: file or directory where to search files
    @param recursive: if True will search also sub-directories
    @param depth: if explore recursively, the depth of sub directories to follow
    @param file_ext: the files extension to get. Default is '.py' (deprecated, use extensions instead)
    @param extensions: list of file extensions to filter by (e.g., ['.py', '.js']). If None, uses file_ext for backward compatibility.
    @return: the file list retrieved. if the input is a file then a one element list.

    """
    file_list = []
    if os.path.isfile(path) or path == '-':
        return [path]
    
    # Use extensions if provided, otherwise fall back to file_ext for backward compatibility
    if extensions is None:
        extensions = [file_ext]
    
    if path[-1] != os.sep:
        path = path + os.sep
    for f in glob.glob(path + "*"):
        if os.path.isdir(f):
            if depth < MAX_DEPTH_RECUR:  # avoid infinite recursive loop
                file_list.extend(get_files_from_dir(f, recursive, depth + 1, file_ext, extensions))
            else:
                continue
        elif any(f.endswith(ext) for ext in extensions):
            file_list.append(f)
    return file_list


def print_processing_progress(filename, pycomment_obj, file_comment, is_folder=False):
    """Print the processing actions for a file with detailed action counts.
    Note: filename should be printed before calling this function.
    
    @param filename: the file being processed
    @param pycomment_obj: the PyComment object that processed the file
    @param file_comment: whether file comment feature is enabled
    @param is_folder: whether processing a folder (affects when to print)
    """
    if filename == '-':
        return
    
    # Count different types of actions (docstrings processed)
    num_classes = 0
    num_functions = 0
    num_file = 0
    
    for e in pycomment_obj.docs_list:
        if e['docs'].element.get('deftype') == 'class':
            num_classes += 1
        elif e['docs'].element.get('deftype') == 'def':
            num_functions += 1
    
    # Check if file docstring was added (use cached result)
    if file_comment and not pycomment_obj._has_module_docstring():
        num_file = 1
    
    # Build action list
    actions = []
    if num_file > 0:
        actions.append("{0} file docstring".format(num_file))
    if num_classes > 0:
        actions.append("{0} class docstring(s)".format(num_classes))
    if num_functions > 0:
        actions.append("{0} function docstring(s)".format(num_functions))
    
    # Print actions on the same line (filename was already printed)
    if actions:
        print(": {0}".format(", ".join(actions)))
    else:
        print(": no actions applied")


def get_config(config_file, encoding='utf-8'):
    """Get the configuration from a file.

    @param config_file: the configuration file
    @param encoding: the encoding to use when reading the config file (default 'utf-8')
    @return: the configuration
    @rtype: dict

    """
    config = {}
    tobool = lambda s: True if s.lower() == 'true' else False
    if config_file:
        try:
            with open(config_file, 'r', encoding=encoding) as f:
                for line in f.readlines():
                    if len(line.strip()):
                        key, value = line.split("=", 1)
                        key, value = key.strip(), value.strip()
                        if key in ['init2class', 'first_line', 'convert_only', 'file_comment']:
                            value = tobool(value)
                        if key == 'indent':
                            value = int(value)
                        config[key] = value
        except:
            print ("Unable to open configuration file '{0}'".format(config_file))
    return config


def run(source, files=[], input_style='auto', output_style='reST', first_line=True, quotes='"""',
        init2class=False, convert=False, config_file=None, ignore_private=False, overwrite=False, spaces=4,
        skip_empty=False, file_comment=False, encoding='utf-8'):
    if input_style == 'auto':
        input_style = None

    config = get_config(config_file, encoding=encoding)
    if 'init2class' in config:
        init2class = config.pop('init2class')
    if 'convert_only' in config:
        convert = config.pop('convert_only')
    if 'quotes' in config:
        quotes = config.pop('quotes')
    if 'input_style' in config:
        input_style = config.pop('input_style')
    if 'output_style' in config:
        output_style = config.pop('output_style')
    if 'first_line' in config:
        first_line = config.pop('first_line')
    if 'file_comment' in config:
        file_comment = config.pop('file_comment')
    if 'encoding' in config:
        encoding = config.pop('encoding')
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
            
            c = PyComment(f, quotes=quotes,
                          input_style=input_style,
                          output_style=output_style,
                          first_line=first_line,
                          ignore_private=ignore_private,
                          convert_only=convert,
                          num_of_spaces=spaces,
                          skip_empty=skip_empty,
                          file_comment=file_comment,
                          encoding=encoding,
                          **config)
            c.proceed()
            if init2class:
                c.docs_init_to_class()

            # Print processing actions on the same line
            print_processing_progress(f, c, file_comment, is_folder=os.path.isdir(source))

            if overwrite:
                list_from, list_to = c.compute_before_after()
                lines_to_write = list_to
            else:
                lines_to_write = c.get_patch_lines(path, path)

            if f == '-':
                sys.stdout.writelines(lines_to_write)
            else:
                if overwrite:
                    if list_from != list_to:
                        c.overwrite_source_file(lines_to_write)
                else:
                    c.write_patch_file(os.path.basename(f) + ".patch", lines_to_write)
        except Exception as e:
            # Print error message and continue to next file
            if f != '-':
                print(f"\nError processing {f}: {str(e)}", file=sys.stderr)
            else:
                print(f"\nError processing stdin: {str(e)}", file=sys.stderr)
            continue


def main():
    desc = 'Pyment v{0} - {1} - {2} - {3}'.format(__version__, __copyright__, __author__, __licence__)
    parser = argparse.ArgumentParser(description='Generates patches after (re)writing docstrings.')
    parser.add_argument('path', type=str,
                        help='python file or folder containing python files to proceed (explore also sub-folders). Use "-" to read from stdin and write to stdout')
    parser.add_argument('-i', '--input', metavar='style', default='auto',
                        dest='input', help='Input docstring style in ["javadoc", "reST", "numpydoc", "google", "auto"] (default autodetected)')
    parser.add_argument('-o', '--output', metavar='style', default="reST",
                        dest='output', help='Output docstring style in ["javadoc", "reST", "numpydoc", "google"] (default "reST")')
    parser.add_argument('-q', '--quotes', metavar='quotes', default='"""',
                        dest='quotes', help='Type of docstring delimiter quotes: \'\'\' or \"\"\" (default \"\"\"). Note that you may escape the characters using \\ like \\\'\\\'\\\', or surround it with the opposite quotes like \"\'\'\'\"')
    parser.add_argument('-f', '--first-line', metavar='status', default="True",
                        dest='first_line', help='Does the comment starts on the first line after the quotes (default "True")')
    parser.add_argument('-t', '--convert', action="store_true", default=False,
                        help="Existing docstrings will be converted but won't create missing ones")
    parser.add_argument('-c', '--config-file', metavar='config', default="",
                        dest='config_file', help='Get a Pyment configuration from a file. Note that the config values will overload the command line ones.')
    parser.add_argument('-d', '--init2class', help='If no docstring to class, then move the __init__ one',
                        action="store_true")
    parser.add_argument('-p', '--ignore-private', metavar='status', default="True",
                        dest='ignore_private', help='Don\'t proceed the private methods/functions starting with __ (two underscores) (default "True")')
    parser.add_argument('-v', '--version', action='version',
                        version=desc)
    parser.add_argument('-w', '--write', action='store_true', dest='overwrite',
                        default=False, help="Don't write patches. Overwrite files instead. If used with path '-' won\'t overwrite but write to stdout the new content instead of a patch/.")
    parser.add_argument('-s', '--spaces', metavar='spaces', dest='spaces', default=4, type=int,
                        help="The default number of spaces to use for indenting on output. Default is 4.")
    parser.add_argument('-e', '--skip-empty', action='store_true', dest='skip_empty',
                        default=False,
                        help="Don't write params, returns, or raises sections if they are empty.")
    parser.add_argument('--file-comment', action='store_true', dest='file_comment',
                        default=False,
                        help="Add a file comment with the file name at the beginning of the file.")
    parser.add_argument('--extensions', metavar='extensions', dest='extensions',
                        default=None,
                        help='Comma-separated list of file extensions to process (e.g., "py,js"). Extensions can include or omit the leading dot.')
    parser.add_argument('--encoding', metavar='encoding', dest='encoding', default='utf-8',
                        help='The encoding to use when reading and writing files (default "utf-8"). Examples: utf-8, latin1, cp1252.')
    # parser.add_argument('-c', '--config', metavar='config_file',
    #                   dest='config', help='Configuration file')

    args = parser.parse_args()
    source = args.path

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

    files = get_files_from_dir(source, extensions=extensions)
    if not files:
        msg = BaseException("No files were found matching {0}".format(args.path))
        raise msg
    if not args.config_file:
        config_file = ''
    else:
        config_file = args.config_file

    tobool = lambda s: True if s.lower() == 'true' else False
    run(source, files, args.input, args.output,
        tobool(args.first_line), args.quotes,
        args.init2class, args.convert, config_file,
        tobool(args.ignore_private), overwrite=args.overwrite,
        spaces=args.spaces, skip_empty=args.skip_empty,
        file_comment=args.file_comment, encoding=args.encoding)


if __name__ == "__main__":
    main()
