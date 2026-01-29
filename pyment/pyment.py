# -*- coding: utf-8 -*-

import os
import re
import difflib
import platform
import sys
import subprocess
import warnings

from .docstring import DocString
from .configs import CommentBuilderConfig, ReadConfig, ActionConfig, CaseConfig

__author__ = "A. Daouzli"
__copyright__ = "Copyright 2012-2021, A. Daouzli; Copyright 2026, V. Schekochihin"
__licence__ = "GPL3"
__version__ = "0.5.0"
__maintainer__ = "A. Daouzli"

#TODO:
# -generate a return if return is used with argument in element
# -generate raises if raises are used
# -generate diagnosis/statistics
# -parse classes public methods and list them in class docstring
# -allow excluding files from processing
# -add managing a unique patch
# -manage docstrings templates
# -manage c/c++ sources
# -accept archives containing source files
# -dev a server that take sources and send back patches


class PyComment(object):
    """This class allow to manage several python scripts docstrings.
    It is used to parse and rewrite in a Pythonic way all the functions', methods' and classes' docstrings.
    The changes are then provided in a patch file.

    """
    def __init__(self,
                 input_file,
                 comment_config:
                 CommentBuilderConfig,
                 read_config: ReadConfig,
                 action_config: ActionConfig,
                 input_style=None,
                 ):
        """Sets the configuration including the source to proceed and options.

        :param input_file: path name (file or folder)
        :param input_style: the type of doctrings format of the output. By default, it will
          autodetect the format for each docstring.
        """
        self.comment_config = comment_config
        self.read_config = read_config
        self.action_config = action_config
        self.file_type = '.py'
        self.filename_list = []
        self.input_file = input_file
        self.input_lines = []  # Need to remember the file when reading off stdin
        self.input_style = input_style
        self.doc_index = -1
        self.file_index = 0
        self.docs_list = []
        self.parsed = False
        self._has_module_docstring_cache = None

    def _get_git_first_commit_author(self, filepath):
        """Get the author of the first commit for a file in a git repository.
        
        :param filepath: path to the file
        :returns: author name if found, None otherwise
        :rtype: str or None
        """
        if filepath == '-' or not os.path.isfile(filepath):
            return None
        
        try:
            # Check if file is in a git repository by finding .git directory
            abs_path = os.path.abspath(filepath)
            current_dir = os.path.dirname(abs_path)
            git_dir = None
            previous_dir = None
            
            # Walk up the directory tree to find .git
            # Continue until we reach the root (when dirname doesn't change)
            while current_dir != previous_dir:
                potential_git = os.path.join(current_dir, '.git')
                if os.path.exists(potential_git):
                    git_dir = current_dir
                    break
                previous_dir = current_dir
                current_dir = os.path.dirname(current_dir)
            
            if not git_dir:
                return None
            
            # Get relative path from git root
            git_root = git_dir
            rel_path = os.path.relpath(abs_path, git_root)
            
            # Get the first commit author for this file
            # Use --reverse to get commits in chronological order, then take the first one
            result = subprocess.run(
                ['git', 'log', '--reverse', '--format=%an', '--', rel_path],
                cwd=git_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                # Get the first line (first commit author)
                author = result.stdout.strip().split('\n')[0]
                return author if author else None
            
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
            # Git command failed or git is not available
            pass
        except Exception:
            # Any other error, silently fail
            pass
        
        return None

    def _has_module_docstring(self):
        """Check if the file already has a module-level docstring at the beginning.
        
        :returns: True if a module-level docstring exists, False otherwise
        :rtype: bool
        """
        # Return cached value if available
        if self._has_module_docstring_cache is not None:
            return self._has_module_docstring_cache
        
        if not self.input_lines:
            self._has_module_docstring_cache = False
            return False
        
        # Skip encoding declarations, blank lines, and imports at the start
        i = 0
        in_docstring = False
        docstring_delimiter = None
        
        while i < len(self.input_lines):
            line = self.input_lines[i]
            stripped = line.strip()
            
            # Skip blank lines
            if not stripped:
                i += 1
                continue
            
            # Skip encoding declarations
            if stripped.startswith('#') and ('coding' in stripped.lower() or 'encoding' in stripped.lower()):
                i += 1
                continue
            
            # Skip imports
            if stripped.startswith('import ') or stripped.startswith('from '):
                i += 1
                continue
            
            # Check if we're already in a docstring
            if in_docstring:
                # Check if this line closes the docstring
                if docstring_delimiter in stripped:
                    self._has_module_docstring_cache = True
                    return True  # Found a complete module docstring
                i += 1
                continue
            
            # Check if this line starts a docstring
            # Look for """ or ''' at the start (possibly with r/u/f prefix)
            if stripped.startswith('"""') or stripped.startswith("'''"):
                in_docstring = True
                docstring_delimiter = '"""' if stripped.startswith('"""') else "'''"
                # Check if it's a single-line docstring
                if stripped.count(docstring_delimiter) >= 2:
                    self._has_module_docstring_cache = True
                    return True
                i += 1
                continue
            
            # Check for r/u/f prefixes
            if len(stripped) >= 4:
                if stripped[0] in ['r', 'u', 'f'] and stripped[1:4] in ['"""', "'''"]:
                    in_docstring = True
                    docstring_delimiter = stripped[1:4]
                    if stripped.count(docstring_delimiter) >= 2:
                        self._has_module_docstring_cache = True
                        return True
                    i += 1
                    continue
                if len(stripped) >= 5 and stripped[0] in ['r', 'u', 'f'] and stripped[1] in ['r', 'u', 'f']:
                    if stripped[2:5] in ['"""', "'''"]:
                        in_docstring = True
                        docstring_delimiter = stripped[2:5]
                        if stripped.count(docstring_delimiter) >= 2:
                            self._has_module_docstring_cache = True
                            return True
                        i += 1
                        continue
            
            # If we hit a def/class/async def, we've passed any module docstring
            if stripped.startswith('def ') or stripped.startswith('class ') or stripped.startswith('async def '):
                self._has_module_docstring_cache = False
                return False
            
            # If we hit any other non-empty line that's not a comment, no module docstring
            if stripped and not stripped.startswith('#'):
                self._has_module_docstring_cache = False
                return False
            
            i += 1
        
        self._has_module_docstring_cache = False
        return False

    def _get_method_scope(self, method_name):
        """Determine the scope of a method based on its name.
        
        :param method_name: the name of the method/function
        :returns: 'public', 'protected', or 'private'
        :rtype: str
        
        """
        if not method_name:
            return 'public'
        
        # Special methods like __init__, __str__, etc. are considered public
        if method_name.startswith('__') and method_name.endswith('__'):
            return 'public'
        
        # Private methods: double leading underscore
        if method_name.startswith('__'):
            return 'private'
        
        # Protected methods: single leading underscore
        if method_name.startswith('_'):
            return 'protected'
        
        # Public methods: no leading underscore
        return 'public'

    def _should_process_method(self, method_name):
        """Check if a method should be processed based on method_scope settings.
        
        :param method_name: the name of the method/function
        :returns: True if the method should be processed, False otherwise
        :rtype: bool
        
        """
        # Check against method_scope filter
        if self.comment_config.method_scope:
            scope = self._get_method_scope(method_name)
            return scope in self.comment_config.method_scope
        
        return True

    def _parse(self):
        """Parses the input file's content and generates a list of its elements/docstrings.

        :returns: the list of elements

        """
        #TODO manage decorators
        #TODO manage default params with strings escaping chars as (, ), ', ', #, ...
        #TODO manage elements ending with comments like: def func(param): # blabla
        elem_list = []
        reading_element = None
        reading_docs = None
        waiting_docs = False
        elem = ''
        raw = ''
        start = 0
        end = 0
        before_lim = ""
        name_part = ''

        try:
            if self.input_file == '-':
                fd = sys.stdin
            else:
                fd = open(self.input_file, 'r', encoding=self.read_config.encoding)

            self.input_lines = fd.readlines()

            if self.input_file != '-':
                fd.close()

        except IOError:
            msg = BaseException('Failed to open file "' + self.input_file + '". Please provide a valid file.')
            raise msg
        for i, ln in enumerate(self.input_lines):
            l = ln.strip()
            if reading_element:
                elem += l
                if l.endswith(':'):
                    reading_element = 'end'
            elif (l.startswith('async def ') or l.startswith('def ') or l.startswith('class ')) and not reading_docs:
                # Extract the name of the method/function/class
                is_method = l.startswith('async def ') or l.startswith('def ')
                if is_method:
                    # Extract method name: find the space after 'def' or 'async def', then get the name
                    if l.startswith('async def '):
                        name_part = l[10:].strip()  # Skip 'async def '
                    else:
                        name_part = l[4:].strip()  # Skip 'def '
                    # Extract name up to '(' or ':'
                    method_name = name_part.split('(')[0].split(':')[0].strip()
                    
                    # Check if this method should be processed
                    if not self._should_process_method(method_name):
                        # If we were still looking for the class docstring, stop
                        # looking.  Otherwise we'll mistake this method's
                        # docstring for the class docstring and mess stuff up!
                        # (See issue #commented_magic_methods).
                        waiting_docs = False
                        continue
                elif l[l.find(' '):].strip().startswith("__") and 'private' not in self.comment_config.method_scope:
                    # For classes, maintain backward compatibility with ignore_private
                    # If we were still looking for the class docstring, stop
                    # looking.  Otherwise we'll mistake this __dunder_method__
                    # docstring for the class docstring and mess stuff up!
                    # (See issue #commented_magic_methods).
                    waiting_docs = False
                    continue
                reading_element = 'start'
                elem = l
                m = re.match(r'^(\s*)[adc]', ln)  # a for async, d for def, c for class
                if m is not None and m.group(1) is not None:
                    spaces: str = m.group(1)
                else:
                    spaces = ''
                # the end of definition should be ':' and eventually a comment following
                # FIXME: but this is missing eventually use of # inside a string value of parameter
                if re.search(r''':(|\s*#[^'"]*)$''', l):
                    reading_element = 'end'
            if reading_element == 'end':
                reading_element = None
                # if currently reading an element content
                waiting_docs = True
                # *** Creates the DocString object ***
                case_config = CaseConfig(
                    spaces=spaces + ' ' * 4,
                    name=name_part,
                    type='def' if is_method else 'class',
                    raw=elem.replace('\n', ' '),
                )
                e = DocString(
                    elem.replace('\n', ' '),
                    comment_config=self.comment_config,
                    case_config=case_config,
                    input_style=self.input_style,
                    )
                elem_list.append({'docs': e, 'location': (-i, -i)})
            else:
                if waiting_docs and ('"""' in l or "'''" in l):
                    # not docstring
                    if not reading_docs and not (
                            l[:3] in ['"""', "'''"] or
                            (l[0] in ['r', 'u', 'f'] and l[1:4] in ['"""', "'''"]) or
                            (l[0] in ['r', 'u', 'f'] and l[1] in ['r', 'u', 'f'] and l[2:5] in ['"""', "'''"])
                    ):
                        waiting_docs = False
                    # start of docstring bloc
                    elif not reading_docs:
                        start = i
                        # determine which delimiter
                        idx_c = l.find('"""')
                        idx_dc = l.find("'''")
                        lim = '"""'
                        if idx_c >= 0 and idx_dc >= 0:
                            if idx_c < idx_dc:
                                lim = '"""'
                            else:
                                lim = "'''"
                        elif idx_c < 0:
                            lim = "'''"
                        reading_docs = lim
                        # check if the docstring starts with 'r', 'u', or 'f' or combination thus extract it
                        if not l.startswith(lim):
                            idx_strip_lim = l.find(lim)
                            idx_abs_lim = ln.find(lim)
                            # remove and keep the prefix r|f|u
                            before_lim = l[:idx_strip_lim]
                            ln = ln[:idx_abs_lim-idx_strip_lim]+ln[idx_abs_lim:]
                        raw = ln
                        # one line docstring
                        if l.count(lim) == 2:
                            end = i
                            elem_list[-1]['docs'].parse_docs(raw, before_lim)
                            elem_list[-1]['location'] = (start, end)
                            reading_docs = None
                            waiting_docs = False
                            reading_element = False
                            raw = ''
                    # end of docstring bloc
                    elif waiting_docs and lim in l:
                        end = i
                        raw += ln
                        elem_list[-1]['docs'].parse_docs(raw, before_lim)
                        elem_list[-1]['location'] = (start, end)
                        reading_docs = None
                        waiting_docs = False
                        reading_element = False
                        raw = ''
                    # inside a docstring bloc
                    elif waiting_docs:
                        raw += ln
                # no docstring found for current element
                elif waiting_docs and l != '' and reading_docs is None:
                    waiting_docs = False
                else:
                    if reading_docs is not None:
                        raw += ln
        if self.action_config.convert_only:
            i = 0
            while i < len(elem_list):
                if elem_list[i]['docs'].get_input_docstring() is None:
                    elem_list.pop(i)
                else:
                    i += 1
        for e in elem_list:
            print('ffff' + repr(e['docs']))
        self.docs_list = elem_list

        self.parsed = True
        return elem_list

    def docs_init_to_class(self):
        """If found a __init__ method's docstring and the class
        without any docstring, so set the class docstring with __init__one,
        and let __init__ without docstring.

        :returns: True if done
        :rtype: boolean

        """
        result = False
        if not self.parsed:
            self._parse()
        einit = []
        eclass = []
        for e in self.docs_list:
            if len(eclass) == len(einit) + 1 and e['docs'].element['name'] == '__init__':
                einit.append(e)
            elif not eclass and e['docs'].element['deftype'] == 'class':
                eclass.append(e)
        for c, i in zip(eclass, einit):
            start, _ = c['location']
            if start < 0:
                start, _ = i['location']
                if start > 0:
                    result = True
                    cspaces = c['docs'].get_spaces()
                    ispaces = i['docs'].get_spaces()
                    c['docs'].set_spaces(ispaces)
                    i['docs'].set_spaces(cspaces)
                    c['docs'].generate_docs()
                    i['docs'].generate_docs()
                    c['docs'], i['docs'] = i['docs'], c['docs']
        return result

    def get_output_docs(self):
        """Return the output docstrings once formatted

        :returns: the formatted docstrings
        :rtype: list

        """
        if not self.parsed:
            self._parse()
        lst = []
        for e in self.docs_list:
            lst.append(e['docs'].get_raw_docs())
        return lst

    def compute_before_after(self):
        """Compute the list of lines before and after the proposed docstring changes.

        :return: tuple of before,after where each is a list of lines of python code.
        """
        if not self.parsed:
            self._parse()
        list_from = self.input_lines
        list_to = []
        
        # Add file comment at the beginning if flag is set and no module docstring exists
        if self.comment_config.file_comment and not self._has_module_docstring():
            if self.input_file != '-':
                filename = os.path.basename(self.input_file)
                # Remove extension from filename
                filename = os.path.splitext(filename)[0]
                
                # Try to get git author of first commit
                author = self._get_git_first_commit_author(self.input_file)
                if author:
                    file_comment_lines = '{0}\n{1}\nAuthor: {2}\n{0}'.format(self.comment_config.quotes, filename, author)
                else:
                    file_comment_lines = '{0}\n{1}\n{0}'.format(self.comment_config.quotes, filename)
            else:
                filename = 'stdin'
                file_comment_lines = '{0}\n{1}\n{0}'.format(self.comment_config.quotes, filename)
            list_to.append(file_comment_lines + '\n')
        
        last = 0
        for e in self.docs_list:
            start, end = e['location']
            if start <= 0:
                start, end = -start, -end
                list_to.extend(list_from[last:start + 1])
            else:
                list_to.extend(list_from[last:start])
            docs = e['docs'].get_raw_docs()
            list_docs = [l + '\n' for l in docs.splitlines()]
            list_to.extend(list_docs)
            last = end + 1
        if last < len(list_from):
            list_to.extend(list_from[last:])

        return list_from, list_to

    def diff(self, source_path='', target_path='', which=-1):
        """Build the diff between original docstring and proposed docstring.

        :type which: int
          -> -1 means all the docstrings of the file
          -> >=0 means the index of the docstring to proceed (Default value = -1)
        :param source_path:  (Default value = '')
        :param target_path:  (Default value = '')
        :returns: the resulted diff
        :rtype: List[str]
        """
        list_from, list_to = self.compute_before_after()

        if source_path.startswith(os.sep):
            source_path = source_path[1:]
        if source_path and not source_path.endswith(os.sep):
            source_path += os.sep
        if target_path.startswith(os.sep):
            target_path = target_path[1:]
        if target_path and not target_path.endswith(os.sep):
            target_path += os.sep

        fromfile = 'a/' + source_path + os.path.basename(self.input_file)
        tofile = 'b/' + target_path + os.path.basename(self.input_file)
        diff_list = difflib.unified_diff(list_from, list_to, fromfile, tofile)
        return [d for d in diff_list]

    def get_patch_lines(self, source_path, target_path):
        """Return the diff between source_path and target_path

        :param source_path: name of the original file (Default value = '')
        :param target_path: name of the final file (Default value = '')

        :return: the diff as a list of \n terminated lines
        :rtype: List[str]
        """
        diff = self.diff(source_path, target_path)

        return ["# Patch generated by Pyment v{0}\n\n".format(__version__)] + diff

    def write_patch_file(self, patch_file, lines_to_write):
        """Write lines_to_write to a the file called patch_file

        :param patch_file: file name of the patch to generate
        :param lines_to_write: lines to write to the file - they should be \n terminated
        :type lines_to_write: list[str]

        :return: None
        """
        with open(patch_file, 'w', encoding=self.read_config.encoding) as f:
            f.writelines(lines_to_write)

    def overwrite_source_file(self, lines_to_write):
        """overwrite the file with line_to_write

        :param lines_to_write: lines to write to the file - they should be \n terminated
        :type lines_to_write: List[str]

        :return: None
        """
        tmp_filename = '{0}.writing'.format(self.input_file)
        ok = False
        try:
            with open(tmp_filename, 'w', encoding=self.read_config.encoding) as fh:
                fh.writelines(lines_to_write)
            ok = True
        finally:
            if ok:
                if platform.system() == 'Windows':
                    self._windows_rename(tmp_filename)
                else:
                    os.rename(tmp_filename, self.input_file)
            else:
                os.unlink(tmp_filename)

    def _windows_rename(self, tmp_filename):
        """ Workaround the fact that os.rename raises an OSError on Windows
        
        :param tmp_filename: The file to rename
    
        """

        os.remove(self.input_file) if os.path.isfile(self.input_file) else None
        os.rename(tmp_filename, self.input_file)

    def proceed(self):
        """Parses the input file and generates/converts the docstrings.

        :return: the list of docstrings
        :rtype: list of dictionaries

        """
        self._parse()
        for e in self.docs_list:
            e['docs'].generate_docs()
        return self.docs_list
