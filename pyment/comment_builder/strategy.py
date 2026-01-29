# -*- coding: utf-8 -*-

"""Strategy pattern implementation for docstring formatting styles."""
from pyment.configs import CaseConfig
from pyment.utils import log_function


class CommentFormatStrategy(object):
    """Base class for docstring formatting strategies.
    
    This defines the interface that all formatting strategies must implement.
    Strategies encapsulate the formatting logic for different docstring styles
    (google, numpydoc, javadoc, reST, groups, etc.).
    """

    def __init__(self, config, case_config):
        """Initialize with CommentBuilderConfig instance."""
        self.config = config
        self.case_config = case_config
    
    def get_key_section_header(self, key, spaces):
        """Get the formatted section header for a given key.
        
        :param key: the section key ('param', 'return', 'raise', etc.)
        :param spaces: leading spaces for indentation
        :return: formatted section header string
        """
        raise NotImplementedError
    
    def get_excluded_sections(self):
        """Get the list of excluded sections.
        
        :return: list of excluded section keys
        """
        raise NotImplementedError
    
    def get_mandatory_sections(self):
        """Get the list of mandatory sections.
        
        :return: list of mandatory section keys
        """
        raise NotImplementedError
    
    def get_optional_sections(self):
        """Get the list of optional sections.
        
        :return: list of optional section keys
        """
        raise NotImplementedError
    
    def format_params_section(self, params):
        """Format the parameters section.
        
        :param params: list of parameter tuples (name, desc, type, default)
        :return: formatted parameters section string
        """
        raise NotImplementedError
    
    def format_return_section(self, return_desc, return_type, params):
        """Format the return section.
        
        :param return_desc: return description (string or list of tuples)
        :param return_type: return type string
        :param params: list of parameters (to check if empty for formatting)
        :return: formatted return section string
        """
        raise NotImplementedError
    
    def format_raises_section(self, raises, params, return_desc):
        """Format the raises section.
        
        :param raises: list of raise tuples (name, desc)
        :param params: list of parameters (to check if empty for formatting)
        :param return_desc: return description (to check if empty for formatting)
        :return: formatted raises section string
        """
        raise NotImplementedError


class NumpydocStrategy(CommentFormatStrategy):
    """Strategy for NumPy-style docstring formatting."""
    
    def __init__(self, config, case_config):
        super().__init__(config, case_config)
        self.tools = config.dst.numpydoc
    
    def get_key_section_header(self, key, spaces):
        """Get NumPy-style section header."""
        return self.tools.get_key_section_header(key, spaces)
    
    def get_excluded_sections(self):
        """Get excluded sections."""
        return self.tools.get_excluded_sections()
    
    def get_mandatory_sections(self):
        """Get mandatory sections."""
        return self.tools.get_mandatory_sections()
    
    def get_optional_sections(self):
        """Get optional sections."""
        return self.tools.get_optional_sections()
    
    def format_params_section(self, params):
        """Format parameters section in NumPy style."""
        raw = '\n'
        if self.config.skip_empty and not params:
            return raw
        
        indent_spaces = ' ' * self.config.num_of_spaces

        def with_space(s):
            lines = []
            for i, l in enumerate(s.splitlines()):
                if i == 0:
                    lines.append(l)
                    continue
                stripped = l.lstrip()
                if not stripped and not self.config.indent_empty_lines:
                    lines.append('')
                else:
                    lines.append(self.case_config.spaces + indent_spaces + stripped)
            return '\n'.join(lines)
        
        raw += self.get_key_section_header('param', self.case_config.spaces)
        for p in params:
            raw += self.case_config.spaces + p[0] + ' :'
            if p[2] is not None and len(p[2]) > 0:
                raw += ' ' + p[2]
            raw += '\n'
            raw += self.case_config.spaces + indent_spaces + with_space(p[1]).strip()
            if len(p) > 2:
                if self.config.show_default_value and 'default' not in p[1].lower() and len(p) > 3 and p[3] is not None:
                    # Add space before default value only if there's a description
                    desc_stripped = p[1].strip() if p[1] else ''
                    space_before = ' ' if desc_stripped else ''
                    raw += space_before + '(Default value = ' + str(p[3]) + ')'
            raw += '\n'
        return raw
    
    def format_return_section(self, return_desc, return_type, params):
        """Format return section in NumPy style."""
        raw = ''
        if self.config.skip_empty and not return_desc:
            return raw
        
        raw += '\n'
        indent_spaces = ' ' * self.config.num_of_spaces

        def with_space(s):
            lines = []
            for i, l in enumerate(s.splitlines()):
                if i == 0:
                    lines.append(l)
                    continue
                stripped = l.lstrip()
                if not stripped and not self.config.indent_empty_lines:
                    lines.append('')
                else:
                    lines.append(self.case_config.spaces + indent_spaces + stripped)
            return '\n'.join(lines)
        
        raw += self.get_key_section_header('return', self.case_config.spaces)
        if return_type:
            rtype = return_type
        else:
            rtype = 'type'
        
        # case of several returns
        if type(return_desc) is list:
            for ret_elem in return_desc:
                # if tuple (name, desc, rtype) else string desc
                if type(ret_elem) is tuple and len(ret_elem) == 3:
                    rtype = ret_elem[2]
                    if rtype is None:
                        rtype = ''
                    raw += self.case_config.spaces
                    if ret_elem[0]:
                        raw += ret_elem[0] + ' : '
                    raw += rtype + '\n' + self.case_config.spaces + indent_spaces + with_space(ret_elem[1]).strip() + '\n'
                else:
                    raw += self.case_config.spaces + rtype + '\n'
                    raw += self.case_config.spaces + indent_spaces + with_space(str(ret_elem)).strip() + '\n'
        # case of a unique return
        elif return_desc is not None:
            raw += self.case_config.spaces + rtype
            raw += '\n' + self.case_config.spaces + indent_spaces + with_space(return_desc).strip() + '\n'
        return raw
    
    def format_raises_section(self, raises, params, return_desc):
        """Format raises section in NumPy style."""
        raw = ''
        if self.config.skip_empty and not raises:
            return raw
        
        if 'raise' not in self.get_excluded_sections():
            raw += '\n'
            if 'raise' in self.get_mandatory_sections() or \
                    (raises and 'raise' in self.get_optional_sections()):
                indent_spaces = ' ' * self.config.num_of_spaces

                def with_space(s):
                    lines = []
                    for i, l in enumerate(s.splitlines()):
                        if i == 0:
                            lines.append(l)
                            continue
                        stripped = l.lstrip()
                        if not stripped and not self.config.indent_empty_lines:
                            lines.append('')
                        else:
                            lines.append(self.case_config.spaces + indent_spaces + stripped)
                    return '\n'.join(lines)
                raw += self.get_key_section_header('raise', self.case_config.spaces)
                if len(raises):
                    for p in raises:
                        raw += self.case_config.spaces + p[0] + '\n'
                        raw += self.case_config.spaces + indent_spaces + with_space(p[1]).strip() + '\n'
                raw += '\n'
        return raw


class GoogleStrategy(CommentFormatStrategy):
    """Strategy for Google-style docstring formatting."""
    
    def __init__(self, config, case_config):
        """Initialize with CommentBuilderConfig instance.
        
        :param config: CommentBuilderConfig instance
        """
        super().__init__(config, case_config)
        self.tools = config.dst.googledoc
    
    def get_key_section_header(self, key, spaces):
        """Get Google-style section header."""
        return self.tools.get_key_section_header(key, spaces)
    
    def get_excluded_sections(self):
        """Get excluded sections."""
        return self.tools.get_excluded_sections()
    
    def get_mandatory_sections(self):
        """Get mandatory sections."""
        return self.tools.get_mandatory_sections()
    
    def get_optional_sections(self):
        """Get optional sections."""
        return self.tools.get_optional_sections()
    
    def format_params_section(self, params):
        """Format parameters section in Google style."""
        raw = '\n'
        if self.config.skip_empty and not params:
            return raw
        
        indent_spaces = ' ' * self.config.num_of_spaces

        def with_space(s):
            lines = []
            for i, l in enumerate(s.splitlines()):
                if i == 0:
                    lines.append(l)
                    continue
                stripped = l.lstrip()
                if not stripped and not self.config.indent_empty_lines:
                    lines.append('')
                else:
                    lines.append(self.case_config.spaces + stripped)
            return '\n'.join(lines)
        
        raw += self.get_key_section_header('param', self.case_config.spaces)
        for p in params:
            raw += self.case_config.spaces + indent_spaces + p[0]
            if p[2] is not None and len(p[2]) > 0:
                raw += ' (' + p[2]
                if len(p) > 3 and p[3] is not None:
                    raw += ', optional'
                raw += ')'
            raw += ': ' + with_space(p[1]).strip()
            if len(p) > 2:
                if self.config.show_default_value and 'default' not in p[1].lower() and len(p) > 3 and p[3] is not None:
                    # Add space before default value only if there's a description
                    desc_stripped = p[1].strip() if p[1] else ''
                    space_before = ' ' if desc_stripped else ''
                    raw += space_before + '(Default value = ' + str(p[3]) + ')'
            raw += '\n'
        return raw
    
    def format_return_section(self, return_desc, return_type, params):
        """Format return section in Google style."""
        raw = ''
        if self.config.skip_empty and not return_desc:
            return raw
        
        raw += '\n'
        indent_spaces = ' ' * self.config.num_of_spaces

        def with_space(s):
            lines = []
            for i, l in enumerate(s.splitlines()):
                if i == 0:
                    lines.append(l)
                    continue
                stripped = l.lstrip()
                if not stripped and not self.config.indent_empty_lines:
                    lines.append('')
                else:
                    lines.append(self.case_config.spaces + indent_spaces + stripped)
            return '\n'.join(lines)
        
        raw += self.get_key_section_header('return', self.case_config.spaces)
        if return_type:
            rtype = return_type
        else:
            rtype = None
        
        # case of several returns
        if type(return_desc) is list:
            for ret_elem in return_desc:
                # if tuple (name=None, desc, rtype) else string desc
                if type(ret_elem) is tuple and len(ret_elem) == 3:
                    rtype = ret_elem[2]
                    if rtype is None:
                        rtype = ''
                    raw += self.case_config.spaces + indent_spaces
                    raw += rtype + ': ' + with_space(ret_elem[1]).strip() + '\n'
                else:
                    if rtype:
                        raw += self.case_config.spaces + indent_spaces + rtype + ': '
                        raw += with_space(str(ret_elem)).strip() + '\n'
                    else:
                        raw += self.case_config.spaces + indent_spaces + with_space(str(ret_elem)).strip() + '\n'
        # case of a unique return
        elif return_desc is not None:
            if rtype:
                raw += self.case_config.spaces + indent_spaces + rtype + ': '
                raw += with_space(return_desc).strip() + '\n'
            else:
                raw += self.case_config.spaces + indent_spaces + with_space(return_desc).strip() + '\n'
        return raw
    
    def format_raises_section(self, raises, params, return_desc):
        """Format raises section in Google style."""
        raw = ''
        if self.config.skip_empty and not raises:
            return raw
        
        if 'raise' not in self.get_excluded_sections():
            raw += '\n'
            if 'raise' in self.get_mandatory_sections() or \
                    (raises and 'raise' in self.get_optional_sections()):
                indent_spaces = ' ' * self.config.num_of_spaces

                def with_space(s):
                    lines = []
                    for i, l in enumerate(s.splitlines()):
                        if i == 0:
                            lines.append(l)
                            continue
                        stripped = l.lstrip()
                        if not stripped and not self.config.indent_empty_lines:
                            lines.append('')
                        else:
                            lines.append(self.case_config.spaces + indent_spaces + stripped)
                    return '\n'.join(lines)
                raw += self.get_key_section_header('raise', self.case_config.spaces)
                if len(raises):
                    for p in raises:
                        raw += self.case_config.spaces + indent_spaces
                        if p[0] is not None:
                            raw += p[0] + ': '
                        if p[1]:
                            raw += p[1].strip()
                        raw += '\n'
                raw += '\n'
        return raw


class DefaultStrategy(CommentFormatStrategy):
    """Default strategy for javadoc, reST, and groups styles."""

    def __init__(self, config, case_config):
        """Initialize with CommentBuilderConfig instance.

        :param config: CommentBuilderConfig instance
        """
        super().__init__(config, case_config)
        self.docs_tools = config.dst
    
    def get_key_section_header(self, key, spaces):
        """Get default section header (empty for default styles)."""
        return ''
    
    def get_excluded_sections(self):
        """Get excluded sections (empty for default)."""
        return []
    
    def get_mandatory_sections(self):
        """Get mandatory sections (empty for default)."""
        return []
    
    def get_optional_sections(self):
        """Get optional sections (empty for default)."""
        return []
    
    @log_function
    def format_params_section(self, params):
        """Format parameters section in default style (javadoc/reST)."""
        raw = '\n'
        if self.config.skip_empty and not params:
            return raw
        
        sep = self.docs_tools.get_sep(target='out')
        sep = sep + ' ' if sep != ' ' else sep
        
        def with_space(s):
            lines = []
            for i, l in enumerate(s.splitlines()):
                if i == 0:
                    lines.append(l)
                    continue
                if not l.strip() and not self.config.indent_empty_lines:
                    lines.append('')
                else:
                    lines.append(self.case_config.spaces + l)
            return '\n'.join(lines)
        
        if len(params):
            for p in params:
                raw += self.case_config.spaces + self.docs_tools.get_key('param', 'out') + ' ' + p[0] + sep + with_space(p[1]).strip()
                if len(p) > 2:
                    if self.config.show_default_value and 'default' not in p[1].lower() and len(p) > 3 and p[3] is not None:
                        # Add space before default value only if there's a description
                        desc_stripped = p[1].strip() if p[1] else ''
                        space_before = ' ' if desc_stripped else ''
                        raw += space_before + '(Default value = ' + str(p[3]) + ')'
                    if self.config.type_tags and p[2] is not None and len(p[2]) > 0:
                        raw += '\n'
                        raw += self.case_config.spaces + self.docs_tools.get_key('type', 'out') + ' ' + p[0] + sep + p[2]
                raw += '\n'
        return raw
    
    def format_return_section(self, return_desc, return_type, params):
        """Format return section in default style (javadoc/reST)."""
        raw = ''
        # If skip_empty is set, we still want to emit a :return: line when
        # there is a return type but type tags are disabled, so treat that
        # case as non-empty.
        if self.config.skip_empty and not return_desc and not (return_type and not self.config.type_tags):
            return raw
        
        sep = self.docs_tools.get_sep(target='out')
        sep = sep + ' ' if sep != ' ' else sep
        
        def with_space(s):
            lines = []
            for i, l in enumerate(s.splitlines()):
                if i == 0:
                    lines.append(l)
                    continue
                if not l.strip() and not self.config.indent_empty_lines:
                    lines.append('')
                else:
                    lines.append(self.case_config.spaces + l)
            return '\n'.join(lines)
        
        if return_desc:
            if not params:
                raw += '\n'
            raw += self.case_config.spaces + self.docs_tools.get_key('return', 'out') + sep + with_space(return_desc.rstrip()).strip() + '\n'
        elif return_type and not self.config.type_tags:
            # When type tags are disabled but a return type exists (e.g. from
            # annotations), still emit a :return: line with an empty description.
            if not params:
                raw += '\n'
            raw += self.case_config.spaces + self.docs_tools.get_key('return', 'out') + sep + '\n'
        if self.config.type_tags and return_type:
            if not params:
                raw += '\n'
            raw += self.case_config.spaces + self.docs_tools.get_key('rtype', 'out') + sep + return_type.rstrip() + '\n'
        return raw
    
    def format_raises_section(self, raises, params, return_desc):
        """Format raises section in default style (javadoc/reST)."""
        raw = ''
        if self.config.skip_empty and not raises:
            return raw
        
        sep = self.docs_tools.get_sep(target='out')
        sep = sep + ' ' if sep != ' ' else sep
        
        def with_space(s):
            lines = []
            for i, l in enumerate(s.splitlines()):
                if i == 0:
                    lines.append(l)
                    continue
                if not l.strip() and not self.config.indent_empty_lines:
                    lines.append('')
                else:
                    lines.append(self.case_config.spaces + l)
            return '\n'.join(lines)
        
        if len(raises):
            if not params and not return_desc:
                raw += '\n'
            for p in raises:
                raw += self.case_config.spaces + self.docs_tools.get_key('raise', 'out') + ' '
                if p[0] is not None:
                    raw += p[0] + sep
                if p[1]:
                    raw += with_space(p[1]).strip()
                raw += '\n'
        raw += '\n'
        return raw


class GroupsStrategy(CommentFormatStrategy):
    """Strategy for groups-style docstring formatting."""

    def __init__(self, config, case_config):
        """Initialize with CommentBuilderConfig instance.

        :param config: CommentBuilderConfig instance
        """
        super().__init__(config, case_config)
        self.docs_tools = config.docs_tools
    
    def get_key_section_header(self, key, spaces):
        """Get groups-style section header (empty)."""
        return ''
    
    def get_excluded_sections(self):
        """Get excluded sections (empty for groups)."""
        return []
    
    def get_mandatory_sections(self):
        """Get mandatory sections (empty for groups)."""
        return []
    
    def get_optional_sections(self):
        """Get optional sections (empty for groups)."""
        return []
    
    def format_params_section(self, params):
        """Format parameters section in groups style (no-op)."""
        return ''
    
    def format_return_section(self, return_desc, return_type, params):
        """Format return section in groups style (no-op)."""
        return ''
    
    def format_raises_section(self, raises, params, return_desc):
        """Format raises section in groups style (no-op)."""
        return ''


def create_strategy(style_name, config, case_config: CaseConfig):
    """Factory function to create the appropriate strategy based on style name.
    
    :param style_name: the output style name ('numpydoc', 'google', 'javadoc', 'reST', 'groups')
    :param config: CommentBuilderConfig instance
    :return: CommentFormatStrategy instance
    """
    if style_name == 'numpydoc':
        return NumpydocStrategy(config, case_config)
    elif style_name == 'google':
        return GoogleStrategy(config, case_config)
    elif style_name == 'groups':
        return GroupsStrategy(config, case_config)
    else:
        # Default for javadoc, reST, etc.
        return DefaultStrategy(config, case_config)

