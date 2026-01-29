#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script to generate spec.json files for each issue folder.
Each spec.json contains:
- get_input_style: detected docstring style
- name: function/method/class name
- description: docstring description
"""

import os
import json
import pyment.pyment as pym

current_dir = os.path.dirname(__file__)
absdir = lambda f: os.path.join(current_dir, f)

# Issue definitions from test_issues.py
ISSUES = [
    ('issue9', 'no_spec_full_comment', {}),
    ('issue10', '10', {}),
    ('issue11', '11', {}),
    ('issue15', '15', {}),
    ('issue19', '19', {}),
    ('issue22', '22', {}),
    ('issue30', '30', {'input_style': 'numpydoc'}),
    ('issue32', '2_spaces', {}),
    ('issue34', '34', {}),
    ('issue46', '46', {}),
    ('issue47', '47', {}),
    ('issue49', 'from_numpydoc', {}),
    ('issue51', 'google_wrong_inner_indentation', {}),
    ('issue58', 'comment_instead_of_return_type', {}),
    ('issue69', 'default_composite', {}),
    ('issue83', 'commented_magic_methods', {'ignore_private': True}),
    ('issue85', 'multiline_param_description', {}),
    ('issue88', 'async_functions', {}),
    ('issue90', 'special_string_types', {}),
    ('issue93', 'complex_type_hints', {}),
    ('issue95', 'params_descriptions_tight', {}),
    ('issue99', 'different_styles_in_one_file', {}),
    ('issue_triplequoted', 'triplequoted', {}),
    ('issue_function_name', 'function_name', {}),
]


def extract_specs(issue_name, folder_name, base_kwargs):
    """Extract specs from an issue file and return as dict"""
    file_path = absdir(os.path.join('cases', folder_name, 'case.py'))
    
    if not os.path.exists(file_path):
        print(f"Warning: File not found: {file_path}")
        return None
    
    try:
        # Parse the file
        p = pym.PyComment(file_path, **base_kwargs)
        p._parse()
        
        if not p.parsed:
            print(f"Warning: Failed to parse {file_path}")
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
                'name': docstring.element.name,
                'deftype': docstring.element.deftype,
                'input_style': docstring.get_input_style() or 'auto',
                'description': docstring.docs['in']['desc'].strip() if docstring.docs['in']['desc'] else ''
            }
            
            specs.append(spec)
        
        return specs if specs else None
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Generate spec.json files for all issues"""
    for issue_name, folder_name, base_kwargs in ISSUES:
        print(f"Processing {issue_name}...")
        specs = extract_specs(issue_name, folder_name, base_kwargs)
        
        if specs is None:
            print(f"  Skipping {issue_name} (no specs extracted)")
            continue
        
        # Write spec.json
        spec_file = absdir(os.path.join('cases', folder_name, 'spec.json'))
        with open(spec_file, 'w', encoding='utf-8') as f:
            json.dump(specs, f, indent=2, ensure_ascii=False)
        
        print(f"  Created {spec_file} with {len(specs)} element(s)")
        for spec in specs:
            print(f"    - {spec['deftype']} {spec['name']}: style={spec['input_style']}, desc={spec['description'][:50]}...")


if __name__ == '__main__':
    main()

