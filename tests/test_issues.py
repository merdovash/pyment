#!/usr/bin/python

import unittest
import os
import json
import re
import argparse
import sys
import pyment.pyment as pym
from parameterized import parameterized

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

# Global filter variables (set by command-line arguments)
_filter_issues = None
_filter_strategies = None
_filter_test_type = None

# all tests is a folder in tests/cases/{folder_name}/case.py
# expceted patch has prefixes tests/cases/{folder_name}/case.py.patch.{strategy}.expected
# Issue definitions: (issue_name, folder_name, base_kwargs, use_proceed)
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
    ('issue47', '47', {'first_line': True}, False, True),
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
    ('case_docs_already_numpydoc', 'docs_already_numpydoc', {}, False, False),
    ('case_docs_already_google', 'docs_already_google', {}, False, False),
    ('case_already_good', 'already_good', {'skip_empty': True}, False, False),
    ('case_already_good_big', 'already_good_big', {'description_on_new_line': True, 'method_scope': 'public', 'file_comment': True}, False, False),
    ('case_comment_by_name_with_args', 'comment_by_name_with_args', {'description-on-new-line': True}, False, False),
    ('issue_type_tags', 'type_tags', {'type_tags': False}, False, False),
    ('issue_no_params', 'no_params', {'type_tags': False, 'description_on_new_line': True, 'method_scope': 'public',}, False, False),
    ('', 'without_indent', {'type_tags': False, 'description_on_new_line': True, 'indent_empty_lines': False}, False, False),
    ('', 'with_indent', {'type_tags': False, 'description_on_new_line': True, 'indent_empty_lines': True}, False, False),
]


def _should_run_issue(issue_name, folder_name):
    """Check if an issue should be run based on filters"""
    if _filter_issues is None:
        return True
    return issue_name in _filter_issues or folder_name in _filter_issues


def _should_run_strategy(strategy):
    """Check if a strategy should be run based on filters"""
    if _filter_strategies is None:
        return True
    return strategy in _filter_strategies


class IssuesTests(unittest.TestCase):
    maxDiff = None
    
    @parameterized.expand([
        (f'{issue_name}_meta', folder_name, base_kwargs, use_proceed, expected_failure)
        for issue_name, folder_name, base_kwargs, use_proceed, expected_failure in ISSUES
        if _should_run_issue(issue_name, folder_name)
    ])
    def test_meta(self, issue_name, folder_name, base_kwargs, use_proceed, expected_failure):
        # Runtime filtering
        if _filter_test_type is not None and _filter_test_type != 'meta':
            self.skipTest(f'Skipped: test-type filter is {_filter_test_type}')
        if not _should_run_issue(issue_name, folder_name):
            self.skipTest(f'Skipped: issue {issue_name} not in filter')

        file_name = os.path.join('cases', folder_name, 'case.py')
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

    @parameterized.expand([
        (folder_name, base_kwargs, use_proceed)
        for issue_name, folder_name, base_kwargs, use_proceed, _ in ISSUES
        if _should_run_issue(issue_name, folder_name)
    ])
    def test_full(self, folder_name, base_kwargs, use_proceed):
        """Parameterized test for all issue tests across all strategies"""
        # Runtime filtering
        if _filter_test_type is not None and _filter_test_type != 'full':
            self.skipTest(f'Skipped: test-type filter is {_filter_test_type}')
        if not _should_run_issue(folder_name, folder_name):
            self.skipTest(f'Skipped: issue {folder_name} not in filter')

        for strategy in STRATEGIES:
            with self.subTest(strategy):
                if not _should_run_strategy(strategy):
                    self.skipTest(f'Skipped: strategy {strategy} not in filter')
                
                # Create kwargs for this strategy
                kwargs = base_kwargs.copy()
                kwargs['output_style'] = strategy
                
                # Build file paths
                file_name = os.path.join('cases', folder_name, 'case.py')
                expected_file = os.path.join('cases', folder_name, f'case.py.patch.{strategy}.expected')
                
                # For expected failures, wrap the test execution
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

        with self.subTest('Status'):
            list_from, list_to = p.compute_before_after()
            self.assertEqual(expected == '', list_from == list_to)
        
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



def parse_arguments():
    """Parse command-line arguments for test filtering"""
    parser = argparse.ArgumentParser(
        description='Run pyment issue tests with optional filtering',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  python test_issues.py

  # Run tests for specific issue(s) by name or folder
  python test_issues.py --issue issue9
  python test_issues.py --issue 9
  python test_issues.py --issue issue9 issue10

  # Run tests for specific strategy(ies)
  python test_issues.py --strategy javadoc
  python test_issues.py --strategy javadoc google

  # Run only meta tests or full tests
  python test_issues.py --test-type meta
  python test_issues.py --test-type full

  # Combine filters
  python test_issues.py --issue issue9 --strategy javadoc
  python test_issues.py --issue 9 --test-type full --strategy reST
        """
    )
    
    parser.add_argument(
        '--issue', '-i',
        nargs='+',
        metavar='ISSUE',
        help='Filter by issue name(s) or folder name(s). Can specify multiple issues.'
    )
    
    parser.add_argument(
        '--strategy', '-s',
        nargs='+',
        choices=STRATEGIES,
        metavar='STRATEGY',
        help=f'Filter by output strategy(ies). Choices: {", ".join(STRATEGIES)}'
    )
    
    parser.add_argument(
        '--test-type', '-t',
        choices=['meta', 'full'],
        metavar='TYPE',
        help='Filter by test type: "meta" (spec.json tests) or "full" (output comparison tests)'
    )
    
    parser.add_argument(
        '--list-issues',
        action='store_true',
        help='List all available issues and exit'
    )
    
    # Parse known args to avoid conflicts with unittest.main()
    args, unittest_args = parser.parse_known_args()
    
    return args, unittest_args


def main():
    global _filter_issues, _filter_strategies, _filter_test_type
    
    args, unittest_args = parse_arguments()
    
    # Handle --list-issues flag
    if args.list_issues:
        print("Available issues:")
        for issue_name, folder_name, _, _, _ in ISSUES:
            print(f"  {issue_name} (folder: {folder_name})")
        sys.exit(0)
    
    # Set global filter variables
    _filter_issues = args.issue
    _filter_strategies = args.strategy
    _filter_test_type = args.test_type
    
    # Validate filters
    if _filter_issues:
        valid_issues = {issue[0] for issue in ISSUES} | {issue[1] for issue in ISSUES}
        invalid_issues = [i for i in _filter_issues if i not in valid_issues]
        if invalid_issues:
            print(f"Warning: Unknown issue(s): {', '.join(invalid_issues)}", file=sys.stderr)
            print(f"Valid issues: {', '.join(sorted(valid_issues))}", file=sys.stderr)
            sys.exit(1)
    
    # Pass remaining arguments to unittest.main()
    sys.argv = [sys.argv[0]] + unittest_args
    unittest.main()


if __name__ == '__main__':
    main()
