#!/usr/bin/python

import json
import os
import re
import unittest

from parameterized import parameterized_class

import pyment.pyment as pym
from pyment.configs import CommentBuilderConfig, ReadConfig, ActionConfig
from pyment.docstring import DocString
from pyment.utils import from_dict

current_dir = os.path.dirname(__file__)
absdir = lambda f: os.path.join(current_dir, f)

# All supported strategies
STRATEGIES = [
    'google',
    'javadoc',
    'numpydoc',
    'reST',
]

# all tests is a folder in tests/cases/{folder_name}/case.py
# expceted patch has prefixes tests/cases/{folder_name}/case.py.patch.{strategy}.expected
# Issue definitions: (issue_name, folder_name, base_kwargs, use_proceed)
ISSUES = [
    ('no_spec_full_comment', {}, False),
    ('10', {}, False),
    ('11', {}, False),
    ('15', {}, False),
    ('19', {}, False),
    ('22', {}, False),
    ('30', {'input_style': 'numpydoc'}, False),
    ('2_spaces', {}, False),
    ('34', {}, False),
    ('46', {}, False),
    ('47', {'first_line': True}, False),
    ('from_numpydoc', {'first_line': True, 'indent_empty_lines': False}, False),
    ('google_wrong_inner_indentation', {'first_line': True, 'indent_empty_lines': False}, False),
    ('comment_instead_of_return_type', {'indent_empty_lines': False}, False),
    ('default_composite', {'indent_empty_lines': False}, False),
    ('commented_magic_methods', {'ignore_private': True}, True),
    ('method_scope_public', {'method_scope': ['public'], 'indent_empty_lines': False}, True),
    ('multiline_param_description', {'indent_empty_lines': False}, False),
    ('async_functions', {'indent_empty_lines': False}, False),
    ('special_string_types', {'indent_empty_lines': False}, False),
    ('complex_type_hints', {'indent_empty_lines': False}, False),
    ('params_descriptions_tight', {'indent_empty_lines': False, 'first_line': True,}, False),
    ('different_styles_in_one_file', {'first_line': True, 'indent_empty_lines': False,}, False),
    ('triplequoted', {'indent_empty_lines': False,}, False),
    ('function_name', {'indent_empty_lines': False}, False),
    ('params', {'indent_empty_lines': False}, False),
    ('free_cases', {}, False),
    ('docs_already_rest', {'indent_empty_lines': False}, False),
    ('docs_already_javadoc', {'indent_empty_lines': False}, False),
    ('docs_already_numpydoc', {'indent_empty_lines': False}, False),
    ('docs_already_google', {'indent_empty_lines': False, 'first_line': True,}, False),
    ('already_good', {'skip_empty': True, 'indent_empty_lines': False, 'type_tags': True}, False),
    ('already_good_big', {'description_on_new_line': True, 'method_scope': 'public', 'file_comment': True, 'indent_empty_lines': False}, False),
    ('comment_by_name_with_args', {'first_line': True, 'indent_empty_lines': False}, False),
    ('type_tags', {'type_tags': False, 'indent_empty_lines': False}, False),
    ('no_params', {'type_tags': False, 'description_on_new_line': True, 'method_scope': 'public', 'indent_empty_lines': False}, False),
    ('without_indent', {'type_tags': False, 'description_on_new_line': True, 'indent_empty_lines': False}, False),
    ('with_indent', {'type_tags': False, 'description_on_new_line': True, 'indent_empty_lines': True}, False),
]


@parameterized_class(
    ("folder_name", "kwargs", "use_proceed"), [
    (folder_name, base_kwargs, use_proceed)
    for folder_name, base_kwargs, use_proceed in ISSUES
])
class Issue(unittest.TestCase):
    maxDiff = None
    
    folder_name: str
    kwargs: dict
    use_proceed: bool
    
    def test_meta(self):
        file_name = os.path.join('cases', self.folder_name, 'case.py')
        spec_data = self._load_spec_json(os.path.join('cases', self.folder_name))
        if spec_data is not None:
            calculated_specs = self._extract_calculated_specs(file_name, self.kwargs)
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

    def test_full(self):
        """Parameterized test for all issue tests across all strategies"""
        for strategy in STRATEGIES:
            with self.subTest(strategy):
                # Create kwargs for this strategy
                kwargs = self.kwargs.copy()
                kwargs['output_style'] = strategy
                
                # Build file paths
                file_name = os.path.join('cases', self.folder_name, 'case.py')
                expected_file = os.path.join('cases', self.folder_name, f'case.py.patch.{strategy}.expected')
                
                # For expected failures, wrap the test execution
                self._run_test(file_name, expected_file, kwargs, self.use_proceed)

    def _run_test(self, file_name, expected_file, kwargs, use_proceed):
        """Helper method to run the actual test"""
        # Load expected result
        expected_path = absdir(expected_file)
        if not os.path.exists(expected_path):
            self.skipTest(f'Expected file not found: {expected_file} (may indicate a known issue)')
        
        with open(expected_path) as f:
            expected = f.read()
        # Strip header if present (for compatibility with old format)
        expected_lines = expected.splitlines(keepends=True)
        if expected_lines and expected_lines[0].startswith("# Patch"):
            expected = "".join(expected_lines[2:])

        comment_config = from_dict(CommentBuilderConfig, kwargs)
        read_config = from_dict(ReadConfig, kwargs)
        action_config = from_dict(ActionConfig, kwargs)

        # Run PyComment
        p = pym.PyComment(absdir(file_name), comment_config, read_config, action_config)
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
        if expected == result:
            # On success, remove .actual file if it exists
            actual_path = absdir(actual_file)
            if os.path.exists(actual_path):
                try:
                    os.remove(actual_path)
                except Exception as e:
                    # If we can't remove the file, log it but don't fail the test
                    print(f"Warning: Could not remove actual file '{actual_file}': {e}")
        else:
            # On failure, write actual result to .actual file
            try:
                with open(absdir(actual_file), 'w') as f:
                    f.write(result)
            except Exception as e:
                # If we can't write the file, log it but don't hide the original error
                print(f"Warning: Could not write actual file '{actual_file}': {e}")
        self.assertEqual(expected, result)

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
        # Parse the file
        comment_config = from_dict(CommentBuilderConfig, base_kwargs)
        read_config = from_dict(ReadConfig, base_kwargs)
        action_config = from_dict(ActionConfig, base_kwargs)
        # Run PyComment
        p = pym.PyComment(absdir(file_name), comment_config, read_config, action_config)
        p._parse()

        if not p.parsed:
            return None

        # Extract specs for each element
        specs = []
        for elem in p.docs_list:
            if elem is None:
                continue

            # Get the DocString object
            docstring: DocString = elem.get('docs')
            if docstring is None:
                continue

            # Parse the docstring if not already parsed
            if not docstring.parsed_docs:
                docstring.parse_docs()

            # Extract information
            spec = {
                'name': docstring.element.name,
                'deftype': docstring.element.deftype,
                'input_style': docstring.get_input_style() or 'auto',
                'description': docstring.docs['in']['desc'].strip() if docstring.docs['in']['desc'] else ''
            }

            specs.append(spec)

        return specs if specs else None
