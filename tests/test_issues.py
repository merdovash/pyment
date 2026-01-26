#!/usr/bin/python

import unittest
import os
import json
import re
import pyment.pyment as pym
from parameterized import parameterized

current_dir = os.path.dirname(__file__)
absdir = lambda f: os.path.join(current_dir, f)

# All supported strategies
STRATEGIES = ['javadoc', 'reST', 'google', 'numpydoc']

# Issue definitions: (issue_name, folder_name, base_kwargs, use_proceed, expected_failure)
ISSUES = [
    ('issue9', '9', {}, False, False),
    ('issue10', '10', {}, False, False),
    ('issue11', '11', {}, False, False),
    ('issue15', '15', {}, False, False),
    ('issue19', '19', {}, False, False),
    ('issue22', '22', {}, False, False),
    ('issue30', '30', {'input_style': 'numpydoc'}, False, False),
    ('issue32', '32', {}, False, False),
    ('issue34', '34', {}, False, True),
    ('issue46', '46', {}, False, False),
    ('issue47', '47', {}, False, True),
    ('issue49', '49', {}, False, False),
    ('issue51', '51', {}, False, False),
    ('issue58', '58', {}, False, False),
    ('issue69', '69', {}, False, False),
    ('issue83', '83', {'ignore_private': True}, True, False),
    ('method_scope_public', 'method_scope_public', {'method_scope': ['public']}, True, False),
    ('issue85', '85', {}, False, False),
    ('issue88', '88', {}, False, False),
    ('issue90', '90', {}, False, False),
    ('issue93', '93', {}, False, False),
    ('issue95', '95', {}, False, False),
    ('issue99', '99', {}, False, False),
    ('issue_triplequoted', 'triplequoted', {}, False, False),
    ('issue_function_name', 'function_name', {}, False, False),
    # FilesConversionTests cases
    ('case_params', 'params', {}, False, False),
    ('case_free_cases', 'free_cases', {}, False, False),
    ('case_docs_already_rest', 'docs_already_rest', {}, False, False),
    ('case_docs_already_javadoc', 'docs_already_javadoc', {}, False, False),
    ('case_docs_already_numpydoc', 'docs_already_numpydoc', {}, False, True),
    ('case_docs_already_google', 'docs_already_google', {}, False, True),
]


class IssuesTests(unittest.TestCase):
    maxDiff = None

    @parameterized.expand([
        (issue_name, folder_name, strategy, base_kwargs, use_proceed, expected_failure)
        for issue_name, folder_name, base_kwargs, use_proceed, expected_failure in ISSUES
        for strategy in STRATEGIES
    ])
    def test_full(self, issue_name, folder_name, strategy, base_kwargs, use_proceed, expected_failure):
        """Parameterized test for all issue tests across all strategies"""
        # Create kwargs for this strategy
        kwargs = base_kwargs.copy()
        kwargs['output_style'] = strategy
        
        # Build file paths
        file_name = os.path.join('cases', folder_name, 'case.py')
        expected_file = os.path.join('cases', folder_name, f'case.py.patch.{strategy}.expected')
        
        # Test spec.json if it exists (only for first strategy to avoid duplication)
        if strategy == STRATEGIES[0]:
            spec_data = self._load_spec_json(os.path.join('cases', folder_name))
            if spec_data is not None:
                calculated_specs = self._extract_calculated_specs(file_name, base_kwargs)
                if calculated_specs is not None:
                    # Compare spec.json with calculated specs
                    with self.subTest(check='spec_json'):
                        self.assertEqual(len(spec_data), len(calculated_specs),
                                       f'Number of elements mismatch: spec.json has {len(spec_data)}, calculated has {len(calculated_specs)}')
                        
                        for i, (spec_item, calc_item) in enumerate(zip(spec_data, calculated_specs)):
                            with self.subTest(element_index=i, element_name=spec_item.get('name', 'unknown')):
                                self.assertEqual(spec_item.get('name'), calc_item.get('name'),
                                               f'Name mismatch for element {i}')
                                self.assertEqual(spec_item.get('deftype'), calc_item.get('deftype'),
                                               f'Deftype mismatch for element {i}')
                                self.assertEqual(spec_item.get('input_style'), calc_item.get('input_style'),
                                               f'Input style mismatch for element {i}: expected {spec_item.get("input_style")}, got {calc_item.get("input_style")}')
                                self.assertEqual(spec_item.get('description'), calc_item.get('description'),
                                               f'Description mismatch for element {i}')
        
        # For expected failures, wrap the test execution
        if expected_failure:
            try:
                self._run_test(file_name, expected_file, kwargs, use_proceed)
                # If we get here, the test passed unexpectedly
                self.fail("Test passed unexpectedly (was marked as expected failure)")
            except AssertionError:
                # Expected failure occurred - this is fine
                pass
        else:
            self._run_test(file_name, expected_file, kwargs, use_proceed)

    def _run_test(self, file_name, expected_file, kwargs, use_proceed):
        """Helper method to run the actual test"""
        # Load expected result
        expected_path = absdir(expected_file)
        if not os.path.exists(expected_path):
            self.skipTest(f'Expected file not found: {expected_file} (may indicate a known issue)')
        
        try:
            with open(expected_path) as f:
                expected = f.read()
            # Strip header if present (for compatibility with old format)
            expected_lines = expected.splitlines(keepends=True)
            if expected_lines and expected_lines[0].startswith("# Patch"):
                expected = "".join(expected_lines[2:])
        except Exception as e:
            self.fail('Raised exception reading expected file: "{0}"'.format(e))
        
        # Run PyComment
        p = pym.PyComment(absdir(file_name), **kwargs)
        if use_proceed:
            p.proceed()
        else:
            p._parse()
            self.assertTrue(p.parsed)
        
        # Get result
        result = ''.join(p.diff())
        
        # For params, remove diff header lines (like in original test_pyment_cases.py)
        # This removes lines like "@@ -1,36 +1,87 @@" which may vary
        if 'params' in file_name:
            expected = self._remove_diff_header(expected)
            result = self._remove_diff_header(result)
        
        # Compare
        actual_file = expected_file.replace('.expected', '.actual')
        try:
            self.assertEqual(expected, result)
            # On success, remove .actual file if it exists
            actual_path = absdir(actual_file)
            if os.path.exists(actual_path):
                try:
                    os.remove(actual_path)
                except Exception as e:
                    # If we can't remove the file, log it but don't fail the test
                    print(f"Warning: Could not remove actual file '{actual_file}': {e}")
        except AssertionError:
            # On failure, write actual result to .actual file
            try:
                with open(absdir(actual_file), 'w') as f:
                    f.write(result)
            except Exception as e:
                # If we can't write the file, log it but don't hide the original error
                print(f"Warning: Could not write actual file '{actual_file}': {e}")
            # Re-raise the original assertion error
            raise

    def _remove_diff_header(self, diff):
        """Remove diff header lines (like @@ -1,36 +1,87 @@) from diff"""
        return re.sub(r'@@.+?@@\n', '', diff)

    def _load_spec_json(self, folder_path):
        """Load spec.json from issue folder"""
        spec_file = absdir(os.path.join(folder_path, 'spec.json'))
        if not os.path.exists(spec_file):
            return None
        
        try:
            with open(spec_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.fail(f'Failed to load spec.json from {folder_path}: {e}')

    def _extract_calculated_specs(self, file_name, base_kwargs):
        """Extract specs from parsed file (same as in generate_specs.py)"""
        try:
            # Parse the file
            p = pym.PyComment(absdir(file_name), **base_kwargs)
            p._parse()
            
            if not p.parsed:
                return None
            
            # Extract specs for each element
            specs = []
            for elem in p.docs_list:
                if elem is None:
                    continue
                
                # Get the DocString object
                docstring = elem.get('docs')
                if docstring is None:
                    continue
                
                # Parse the docstring if not already parsed
                if not docstring.parsed_docs:
                    docstring.parse_docs()
                
                # Extract information
                spec = {
                    'name': docstring.element.get('name', ''),
                    'deftype': docstring.element.get('deftype', ''),
                    'input_style': docstring.get_input_style() or 'auto',
                    'description': docstring.docs['in']['desc'].strip() if docstring.docs['in']['desc'] else ''
                }
                
                specs.append(spec)
            
            return specs if specs else None
            
        except Exception as e:
            self.fail(f'Failed to extract specs from {file_name}: {e}')


def main():
    unittest.main()


if __name__ == '__main__':
    main()
