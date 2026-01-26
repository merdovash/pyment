# -*- coding: utf-8 -*-
import os
import re
import subprocess
import sys
import tempfile
import json
import unittest

from parameterized import parameterized

import pyment.pyment


class AppTestsBase(unittest.TestCase):
    """
    Base class for app tests with common functionality.
    """

    # You have to run this as a module when testing so the relative imports work.
    CMD_PREFIX = sys.executable + ' -m pyment.pymentapp {}'

    RE_TYPE = type(re.compile('get the type to test if an argument is an re'))

    # cwd to use when running subprocess.
    # It has to be at the repo directory so python -m can be used
    CWD = os.path.dirname(os.path.dirname(__file__))

    @classmethod
    def absdir(cls, f):
        """Get absolute path relative to test directory"""
        return os.path.join(os.path.dirname(__file__), f)

    @classmethod
    def normalise_empty_lines(cls, lines):
        """
            Replace any lines that are only whitespace with a single \n

            textwrap.dedent removes all whitespace characters on lines only containing whitespaces
            see: https://bugs.python.org/issue30754

            And some people set their editors to strip trailing white space.

            But sometimes there is a space on an empty line in the output which will fail the comparison.

            So strip the spaces on empty lines

        :param lines: string of lines to normalise
        :type lines: str

        :return: normalised lines
        """

        return re.sub('^\s+$', '', lines, flags=re.MULTILINE)

    def run_command(self, cmd_to_run, write_to_stdin=None):
        """
        Run a command in shell mode returning stdout, stderr and the returncode.

        :param cmd_to_run: shell command to run
        :type cmd_to_run: str

        :param write_to_stdin: string to put on stdin if not None
        :type write_to_stdin: str | None

        :return: stdout, stderr, returncode
        :rtype: (str, str, int)
        """

        p = subprocess.Popen(
            cmd_to_run, shell=True, cwd=self.CWD,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if write_to_stdin:
            # Python3 compatibility - input has to be bytes
            write_to_stdin = write_to_stdin.encode()

        stdout, stderr = p.communicate(write_to_stdin)

        if isinstance(stdout, bytes):
            # Python 3 compatibility - output will be bytes
            stdout = stdout.decode()
            stderr = stderr.decode()

        return stdout, stderr, p.returncode

    def _load_spec_json(self, folder_path):
        """Load spec.json from args case folder"""
        spec_file = self.absdir(os.path.join('args_cases', folder_path, 'spec.json'))
        if not os.path.exists(spec_file):
            return None
        
        try:
            with open(spec_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.fail(f'Failed to load spec.json from {folder_path}: {e}')

    def _load_input_file(self, folder_path):
        """Load case.py input file"""
        input_file = self.absdir(os.path.join('args_cases', folder_path, 'case.py'))
        if not os.path.exists(input_file):
            return None
        
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.fail(f'Failed to load input file from {folder_path}: {e}')

    def _load_expected_file(self, folder_path, file_type):
        """Load expected output file (patch or overwrite)"""
        if file_type == 'patch':
            expected_file = self.absdir(os.path.join('args_cases', folder_path, 'case.py.patch.expected'))
        elif file_type == 'overwrite':
            expected_file = self.absdir(os.path.join('args_cases', folder_path, 'case.py.overwrite.expected'))
        else:
            return None
        
        if not os.path.exists(expected_file):
            return None
        
        try:
            with open(expected_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.fail(f'Failed to load expected file from {folder_path}: {e}')

    def _check_python_version(self, spec):
        """Check if test should run based on Python version"""
        py_version = sys.version_info[:2]
        
        if spec.get('python_version_min'):
            min_version_str = spec['python_version_min'].split('.')
            min_version = (int(min_version_str[0]), int(min_version_str[1]))
            if py_version < min_version:
                return False
        
        if spec.get('python_version_max'):
            max_version_str = spec['python_version_max'].split('.')
            max_version = (int(max_version_str[0]), int(max_version_str[1]))
            if py_version >= max_version:
                return False
        
        return True

    def _get_actual_file_path(self, folder_path, file_type):
        """Get path for .actual file"""
        if file_type == 'patch':
            return self.absdir(os.path.join('args_cases', folder_path, 'case.py.patch.actual'))
        elif file_type == 'overwrite':
            return self.absdir(os.path.join('args_cases', folder_path, 'case.py.overwrite.actual'))
        elif file_type == 'stderr':
            return self.absdir(os.path.join('args_cases', folder_path, 'stderr.actual'))
        else:
            return None

    def _write_actual_file(self, folder_path, content, file_type):
        """Write actual output to .actual file"""
        actual_path = self._get_actual_file_path(folder_path, file_type)
        if actual_path:
            try:
                with open(actual_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                print(f"Warning: Could not write actual file '{actual_path}': {e}")

    def _remove_actual_file(self, folder_path, file_type):
        """Remove .actual file if it exists"""
        actual_path = self._get_actual_file_path(folder_path, file_type)
        if actual_path and os.path.exists(actual_path):
            try:
                os.remove(actual_path)
            except Exception as e:
                print(f"Warning: Could not remove actual file '{actual_path}': {e}")


class NoArgsTests(AppTestsBase):
    """Test cases for no arguments scenarios"""

    ARGS_CASES = [
        ('no_args_lt_py33', 'no_args_lt_py33'),
        ('no_args_ge_py33', 'no_args_ge_py33'),
    ]

    @parameterized.expand([
        (case_name, folder_name)
        for case_name, folder_name in ARGS_CASES
    ])
    def test_no_args(self, case_name, folder_name):
        """Test no arguments case"""
        spec = self._load_spec_json(folder_name)
        if spec is None:
            self.skipTest(f'No spec.json found for {folder_name}')
        
        # Check Python version requirements
        if not self._check_python_version(spec):
            self.skipTest(f'Python version requirement not met for {folder_name}')
        
        cmd_args = spec.get('cmd_args', '')
        expected_stderr_regex = spec.get('expected_stderr_regex', '')
        expected_returncode = spec.get('expected_returncode', 2)
        
        cmd_to_run = self.CMD_PREFIX.format(cmd_args)
        
        stdout, stderr, returncode = self.run_command(cmd_to_run, write_to_stdin=None)
        
        # Check return code
        try:
            self.assertEqual(returncode, expected_returncode, 
                            f'Expected return code {expected_returncode}, got {returncode}')
        except AssertionError:
            self._write_actual_file(folder_name, stderr, 'stderr')
            raise
        
        # Check stderr matches regex
        if expected_stderr_regex:
            try:
                pattern = re.compile(expected_stderr_regex, re.DOTALL)
                self.assertIsNotNone(pattern.search(stderr),
                                   f'Stderr did not match regex: {expected_stderr_regex}\nGot: {stderr!r}')
                # On success, remove .actual file if it exists
                self._remove_actual_file(folder_name, 'stderr')
            except AssertionError:
                self._write_actual_file(folder_name, stderr, 'stderr')
                raise


class StdinPatchTests(AppTestsBase):
    """Test cases for stdin patch mode"""

    ARGS_CASES = [
        ('stdin_patch_mode', 'stdin_patch_mode'),
    ]

    @parameterized.expand([
        (case_name, folder_name)
        for case_name, folder_name in ARGS_CASES
    ])
    def test_stdin_patch(self, case_name, folder_name):
        """Test stdin patch mode"""
        spec = self._load_spec_json(folder_name)
        if spec is None:
            self.skipTest(f'No spec.json found for {folder_name}')
        
        input_content = self._load_input_file(folder_name)
        expected_output = self._load_expected_file(folder_name, 'patch')
        
        if input_content is None or expected_output is None:
            self.skipTest(f'Missing input or expected file for {folder_name}')
        
        cmd_args = spec.get('cmd_args', '-')
        output_format = spec.get('output_format')
        
        cmd_to_run = self.CMD_PREFIX.format(cmd_args)
        if output_format:
            cmd_to_run = f'{cmd_to_run} --output {output_format}'
        
        stdout, stderr, returncode = self.run_command(cmd_to_run, write_to_stdin=input_content)
        
        try:
            self.assertEqual(returncode, spec.get('expected_returncode', 0))
            self.assertEqual(stderr, spec.get('expected_stderr', ''))
            
            # Normalize and compare stdout
            got = self.normalise_empty_lines(stdout).replace('\r\n', '\n')
            expected = self.normalise_empty_lines(expected_output)
            
            self.assertEqual(got, expected,
                            f'Stdout mismatch:\nExpected:\n{expected!r}\nGot:\n{got!r}')
            # On success, remove .actual file if it exists
            self._remove_actual_file(folder_name, 'patch')
        except AssertionError:
            # On failure, write actual result to .actual file
            self._write_actual_file(folder_name, stdout, 'patch')
            raise


class StdinOverwriteTests(AppTestsBase):
    """Test cases for stdin overwrite mode"""

    ARGS_CASES = [
        ('stdin_overwrite', 'stdin_overwrite'),
    ]

    @parameterized.expand([
        (case_name, folder_name)
        for case_name, folder_name in ARGS_CASES
    ])
    def test_stdin_overwrite(self, case_name, folder_name):
        """Test stdin overwrite mode"""
        spec = self._load_spec_json(folder_name)
        if spec is None:
            self.skipTest(f'No spec.json found for {folder_name}')
        
        input_content = self._load_input_file(folder_name)
        expected_output = self._load_expected_file(folder_name, 'overwrite')
        
        if input_content is None or expected_output is None:
            self.skipTest(f'Missing input or expected file for {folder_name}')
        
        cmd_args = spec.get('cmd_args', '-w -')
        output_format = spec.get('output_format')
        
        cmd_to_run = self.CMD_PREFIX.format(cmd_args)
        if output_format:
            cmd_to_run = f'{cmd_to_run} --output {output_format}'
        
        stdout, stderr, returncode = self.run_command(cmd_to_run, write_to_stdin=input_content)
        
        try:
            self.assertEqual(returncode, spec.get('expected_returncode', 0))
            self.assertEqual(stderr, spec.get('expected_stderr', ''))
            
            # Normalize and compare stdout
            got = self.normalise_empty_lines(stdout).replace('\r\n', '\n')
            expected = self.normalise_empty_lines(expected_output)
            
            self.assertEqual(got, expected,
                            f'Stdout mismatch:\nExpected:\n{expected!r}\nGot:\n{got!r}')
            # On success, remove .actual file if it exists
            self._remove_actual_file(folder_name, 'overwrite')
        except AssertionError:
            # On failure, write actual result to .actual file
            self._write_actual_file(folder_name, stdout, 'overwrite')
            raise


class FileOverwriteTests(AppTestsBase):
    """Test cases for file overwrite mode"""

    ARGS_CASES = [
        ('overwrite_same', 'overwrite_same'),
        ('overwrite_different', 'overwrite_different'),
    ]

    @parameterized.expand([
        (case_name, folder_name)
        for case_name, folder_name in ARGS_CASES
    ])
    def test_file_overwrite(self, case_name, folder_name):
        """Test file overwrite mode"""
        spec = self._load_spec_json(folder_name)
        if spec is None:
            self.skipTest(f'No spec.json found for {folder_name}')
        
        input_content = self._load_input_file(folder_name)
        expected_output = self._load_expected_file(folder_name, 'overwrite')
        
        if input_content is None or expected_output is None:
            self.skipTest(f'Missing input or expected file for {folder_name}')
        
        # Create temporary file
        input_fd, input_filename = tempfile.mkstemp(suffix='.py', text=True)
        try:
            with os.fdopen(input_fd, 'w') as f:
                f.write(input_content)
            
            cmd_args = spec.get('cmd_args', '')
            output_format = spec.get('output_format')
            overwrite_mode = spec.get('overwrite_mode', True)
            
            full_cmd_args = f'{cmd_args} {input_filename}'
            if overwrite_mode:
                full_cmd_args = f'{full_cmd_args} -w'
            
            cmd_to_run = self.CMD_PREFIX.format(full_cmd_args)
            if output_format:
                cmd_to_run = f'{cmd_to_run} --output {output_format}'
            
            stdout, stderr, returncode = self.run_command(cmd_to_run)
            
            try:
                self.assertEqual(returncode, spec.get('expected_returncode', 0))
                self.assertEqual(stderr, spec.get('expected_stderr', ''))
                
                # Read the overwritten file
                with open(input_filename, 'r') as f:
                    output = f.read()
                
                got = self.normalise_empty_lines(output)
                expected = self.normalise_empty_lines(expected_output)
                
                self.assertEqual(got, expected,
                              f'File content mismatch:\nExpected:\n{expected!r}\nGot:\n{got!r}')
                # On success, remove .actual file if it exists
                self._remove_actual_file(folder_name, 'overwrite')
            except AssertionError:
                # On failure, write actual result to .actual file
                with open(input_filename, 'r') as f:
                    output = f.read()
                self._write_actual_file(folder_name, output, 'overwrite')
                raise
        finally:
            if os.path.exists(input_filename):
                os.remove(input_filename)


class FilePatchTests(AppTestsBase):
    """Test cases for file patch mode"""

    ARGS_CASES = [
        ('patch_same', 'patch_same'),
        ('patch_different', 'patch_different'),
    ]

    @parameterized.expand([
        (case_name, folder_name)
        for case_name, folder_name in ARGS_CASES
    ])
    def test_file_patch(self, case_name, folder_name):
        """Test file patch mode"""
        spec = self._load_spec_json(folder_name)
        if spec is None:
            self.skipTest(f'No spec.json found for {folder_name}')
        
        input_content = self._load_input_file(folder_name)
        expected_output = self._load_expected_file(folder_name, 'patch')
        
        if input_content is None or expected_output is None:
            self.skipTest(f'Missing input or expected file for {folder_name}')
        
        # Create temporary file
        input_fd, input_filename = tempfile.mkstemp(suffix='.py', text=True)
        patch_filename = os.path.join(self.CWD, os.path.basename(input_filename) + '.patch')
        
        try:
            with os.fdopen(input_fd, 'w') as f:
                f.write(input_content)
            
            cmd_args = spec.get('cmd_args', '')
            output_format = spec.get('output_format')
            
            full_cmd_args = f'{cmd_args} {input_filename}'
            cmd_to_run = self.CMD_PREFIX.format(full_cmd_args)
            if output_format:
                cmd_to_run = f'{cmd_to_run} --output {output_format}'
            
            stdout, stderr, returncode = self.run_command(cmd_to_run)
            
            try:
                self.assertEqual(returncode, spec.get('expected_returncode', 0))
                self.assertEqual(stderr, spec.get('expected_stderr', ''))
                
                # Read the patch file
                if os.path.exists(patch_filename):
                    with open(patch_filename, 'r') as f:
                        output = f.read()
                    
                    # Replace filename in output with '-' to match expected
                    output = re.sub(
                        r'/{}$'.format(os.path.basename(input_filename)),
                        r'/-',
                        output,
                        flags=re.MULTILINE
                    )
                    
                    got = self.normalise_empty_lines(output)
                    expected = self.normalise_empty_lines(expected_output)
                    
                    self.assertEqual(got, expected,
                                  f'Patch file mismatch:\nExpected:\n{expected!r}\nGot:\n{got!r}')
                    # On success, remove .actual file if it exists
                    self._remove_actual_file(folder_name, 'patch')
                else:
                    self.fail(f'Patch file was not created: {patch_filename}')
            except AssertionError:
                # On failure, write actual result to .actual file
                if os.path.exists(patch_filename):
                    with open(patch_filename, 'r') as f:
                        output = f.read()
                    # Replace filename in output with '-' to match expected
                    output = re.sub(
                        r'/{}$'.format(os.path.basename(input_filename)),
                        r'/-',
                        output,
                        flags=re.MULTILINE
                    )
                    self._write_actual_file(folder_name, output, 'patch')
                raise
        finally:
            if os.path.exists(input_filename):
                os.remove(input_filename)
            if os.path.exists(patch_filename):
                os.remove(patch_filename)


class PreCommitHookTests(AppTestsBase):
    """Test cases for pre-commit hook behavior
    
    Pre-commit passes files as command line arguments. The hook should:
    1. Process all files passed as arguments
    2. Return exit code 0 if no changes are needed
    3. Return exit code 1 if changes are needed
    """

    def _load_precommit_spec(self, folder_path):
        """Load spec.json from precommit hook test folder"""
        spec_file = self.absdir(os.path.join('args_cases', folder_path, 'spec.json'))
        if not os.path.exists(spec_file):
            return None
        
        try:
            with open(spec_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.fail(f'Failed to load spec.json from {folder_path}: {e}')

    def _load_precommit_file(self, folder_path, filename):
        """Load a file from precommit hook test folder"""
        file_path = self.absdir(os.path.join('args_cases', folder_path, filename))
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.fail(f'Failed to load file {filename} from {folder_path}: {e}')

    def test_precommit_hook_single_file_with_changes(self):
        """Test pre-commit hook with a single file that needs changes"""
        folder_name = 'precommit_hook'
        spec = self._load_precommit_spec(folder_name)
        if spec is None:
            self.skipTest(f'No spec.json found for {folder_name}')
        
        # Create temporary file with changes needed
        input_content = self._load_precommit_file(folder_name, 'file_with_changes.py')
        if input_content is None:
            self.skipTest(f'Missing input file for {folder_name}')
        
        input_fd, input_filename = tempfile.mkstemp(suffix='.py', text=True)
        try:
            with os.fdopen(input_fd, 'w') as f:
                f.write(input_content)
            
            output_format = spec.get('output_format', 'google')
            cmd_to_run = f'{self.CMD_PREFIX.format(input_filename)} --output {output_format}'
            
            stdout, stderr, returncode = self.run_command(cmd_to_run)
            
            # Should return 1 (or 2 if argparse error) because file needs changes
            # Current implementation may fail with argparse error if multiple files passed
            # But single file should work
            expected_returncode = spec.get('expected_returncode_with_changes', 1)
            
            # Check if we got expected return code or argparse error (code 2)
            # If argparse error, that's the bug we're testing for
            if returncode == 2:
                # This indicates argparse error - the hook doesn't support multiple files
                self.fail(f'Argparse error when processing file (return code 2). '
                         f'This indicates the hook may not support multiple files as pre-commit passes them. '
                         f'Stderr: {stderr}')
            
            self.assertEqual(returncode, expected_returncode,
                           f'Expected return code {expected_returncode}, got {returncode}. '
                           f'Stdout: {stdout}, Stderr: {stderr}')
        finally:
            if os.path.exists(input_filename):
                os.remove(input_filename)

    def test_precommit_hook_single_file_without_changes(self):
        """Test pre-commit hook with a single file that doesn't need changes"""
        folder_name = 'precommit_hook'
        spec = self._load_precommit_spec(folder_name)
        if spec is None:
            self.skipTest(f'No spec.json found for {folder_name}')
        
        # Create temporary file without changes needed
        input_content = self._load_precommit_file(folder_name, 'file_without_changes.py')
        if input_content is None:
            self.skipTest(f'Missing input file for {folder_name}')
        
        input_fd, input_filename = tempfile.mkstemp(suffix='.py', text=True)
        try:
            with os.fdopen(input_fd, 'w') as f:
                f.write(input_content)
            
            output_format = spec.get('output_format', 'google')
            cmd_to_run = f'{self.CMD_PREFIX.format(input_filename)} --output {output_format}'
            
            stdout, stderr, returncode = self.run_command(cmd_to_run)
            
            # Should return 0 because file doesn't need changes
            expected_returncode = spec.get('expected_returncode_without_changes', 0)
            
            self.assertEqual(returncode, expected_returncode,
                           f'Expected return code {expected_returncode}, got {returncode}. '
                           f'Stdout: {stdout}, Stderr: {stderr}')
        finally:
            if os.path.exists(input_filename):
                os.remove(input_filename)

    def test_precommit_hook_multiple_files(self):
        """Test pre-commit hook with multiple files (as pre-commit actually passes them)
        
        This test simulates how pre-commit actually calls the hook:
        pyment file1.py file2.py file3.py
        
        After fix, this should work correctly with multiple files as positional arguments.
        """
        folder_name = 'precommit_hook'
        spec = self._load_precommit_spec(folder_name)
        if spec is None:
            self.skipTest(f'No spec.json found for {folder_name}')
        
        # Create temporary files
        file_with_changes = self._load_precommit_file(folder_name, 'file_with_changes.py')
        file_without_changes = self._load_precommit_file(folder_name, 'file_without_changes.py')
        
        if file_with_changes is None or file_without_changes is None:
            self.skipTest(f'Missing input files for {folder_name}')
        
        input_fd1, input_filename1 = tempfile.mkstemp(suffix='.py', text=True)
        input_fd2, input_filename2 = tempfile.mkstemp(suffix='.py', text=True)
        
        try:
            with os.fdopen(input_fd1, 'w') as f:
                f.write(file_with_changes)
            with os.fdopen(input_fd2, 'w') as f:
                f.write(file_without_changes)
            
            output_format = spec.get('output_format', 'google')
            # Simulate pre-commit passing multiple files as arguments
            # After fix, this should work correctly
            cmd_to_run = f'{sys.executable} -m pyment.pymentapp --output {output_format} {input_filename1} {input_filename2}'
            
            stdout, stderr, returncode = self.run_command(cmd_to_run)
            
            # After fix, should return 1 because at least one file needs changes
            expected_returncode = spec.get('expected_returncode_with_changes', 1)
            self.assertEqual(returncode, expected_returncode,
                           f'Expected return code {expected_returncode}, got {returncode}. '
                           f'Stdout: {stdout}, Stderr: {stderr}')
        finally:
            if os.path.exists(input_filename1):
                os.remove(input_filename1)
            if os.path.exists(input_filename2):
                os.remove(input_filename2)