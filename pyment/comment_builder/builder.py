# -*- coding: utf-8 -*-

from .config import CommentBuilderConfig


class CommentBuilder(object):
    """Base class for building docstring comments.
    
    This class provides common functionality for building docstrings
    in various formats (javadoc, reST, google, numpydoc, etc.).
    """
    
    __slots__ = (
        'config', 'strategy', 'description', 'params', 'return_desc', 'return_type', 'raises',
        'post', 'doctests', 'element_name', 'input_raw',
        'is_auto_generated_name', 'has_existing_description'
    )
    
    def __init__(self, config, strategy):
        """Initialize the builder with configuration and strategy.
        
        :param config: CommentBuilderConfig instance containing all configuration
        :param strategy: CommentFormatStrategy instance for formatting
        """
        self.config = config
        self.strategy = strategy
        
        # Data to build (set by setters)
        self.description = ''
        self.params = []
        self.return_desc = None
        self.return_type = None
        self.raises = []
        self.post = ''
        self.doctests = ''
        self.element_name = None
        self.input_raw = None
        self.is_auto_generated_name = False
        self.has_existing_description = False
        
    def set_name(self, name):
        """Set the element name. Description is set to the name as-is.
        
        :param name: the element name
        :return: self for method chaining
        """
        self.element_name = name
        self.description = name if name else ''
        return self
        
    def set_description(self, desc, has_existing=False):
        """Set the description text directly.
        
        :param desc: description text
        :param has_existing: whether this description came from an existing docstring
        :return: self for method chaining
        """
        self.description = desc
        self.has_existing_description = has_existing
        return self
        
    def set_params(self, params):
        """Set the parameters list. Each param is (name, desc, type, default).
        
        :param params: list of parameter tuples
        :return: self for method chaining
        """
        self.params = params
        return self
        
    def set_return(self, return_desc, return_type=None):
        """Set the return description and type.
        
        :param return_desc: return description
        :param return_type: return type (optional)
        :return: self for method chaining
        """
        self.return_desc = return_desc
        self.return_type = return_type
        return self
        
    def set_raises(self, raises):
        """Set the raises list. Each raise is (name, desc).
        
        :param raises: list of raise tuples
        :return: self for method chaining
        """
        self.raises = raises
        return self
        
    def set_post(self, post):
        """Set the post section content.
        
        :param post: post section content
        :return: self for method chaining
        """
        self.post = post
        return self
        
    def set_doctests(self, doctests):
        """Set the doctests content.
        
        :param doctests: doctests content
        :return: self for method chaining
        """
        self.doctests = doctests
        return self
        
    def set_element_info(self, name, input_raw=None, is_auto_generated=False):
        """Set element information.
        
        :param name: element name
        :param input_raw: raw input docstring (optional)
        :param is_auto_generated: whether name is auto-generated (optional)
        :return: self for method chaining
        """
        self.element_name = name
        self.input_raw = input_raw
        self.is_auto_generated_name = is_auto_generated
        return self
        
    def _build_params_section(self, sep):
        """Build the parameters section.
        
        :param sep: separator for current style (kept for compatibility, may be unused)
        :return: formatted parameters section
        """
        return self.strategy.format_params_section(self.params)
        
    def _build_return_section(self, sep):
        """Build the return section.
        
        :param sep: separator for current style (kept for compatibility, may be unused)
        :return: formatted return section
        """
        return self.strategy.format_return_section(
            self.return_desc,
            self.return_type,
            self.params
        )
        
    def _build_raises_section(self, sep):
        """Build the raises section.
        
        :param sep: separator for current style (kept for compatibility, may be unused)
        :return: formatted raises section
        """
        return self.strategy.format_raises_section(
            self.raises,
            self.params,
            self.return_desc
        )
    
    def _should_use_one_line_format_with_spaces(self):
        """Determine if auto-generated docstrings should use one-line format with spaces.
        
        This method can be overridden in subclasses to provide element-specific behavior.
        By default, returns False (standard formatting).
        
        :return: True if one-line format with spaces should be used, False otherwise
        """
        return False
    
    def _has_sections(self):
        """Check if docstring has any sections (params, return, raises).
        
        :return: True if any sections are present, False otherwise
        """
        return bool(self.params or self.return_desc or self.return_type or self.raises)
    
    def _with_space(self, text):
        """Add indentation to all lines except the first.
        
        :param text: text to indent
        :return: indented text
        """
        return '\n'.join([self.config.spaces + l if i > 0 else l for i, l in enumerate(text.splitlines())])
    
    def _build_docstring_start(self):
        """Build the initial docstring opening with quotes.
        
        :return: opening string with quotes
        """
        return self.config.spaces + self.config.before_lim + self.config.quotes
    
    def _build_single_line_docstring(self, desc):
        """Build a single-line docstring without sections.
        
        :param desc: description text
        :return: complete single-line docstring
        """
        raw = self._build_docstring_start()
        
        if self.config.description_on_new_line:
            # Put description on its own line and close on a new line as well
            raw += '\n' + self.config.spaces + (desc if desc else self.config.trailing_space)
            raw += '\n' + self.config.spaces + self.config.quotes
        elif self.is_auto_generated_name and self._should_use_one_line_format_with_spaces():
            # For classes with only class name, always use one-line format with spaces
            raw += ' ' + desc + ' ' + self.config.quotes
        elif self.is_auto_generated_name and self.config.first_line:
            # For auto-generated descriptions with first_line=True, put description on same line
            raw += desc if desc else self.config.trailing_space
            if self.element_name == '__init__':
                raw += '\n\n' + self.config.spaces + self.config.quotes
            else:
                raw += '\n' + self.config.spaces + self.config.quotes
        else:
            # Keep it on one line with triple quotes
            raw += desc if desc else self.config.trailing_space
            raw += self.config.quotes
        
        return raw.rstrip()
    
    def _build_multi_line_description_only(self, desc):
        """Build a multi-line docstring without sections.
        
        :param desc: description text
        :return: complete multi-line docstring
        """
        raw = self._build_docstring_start()
        
        if not self.config.first_line:
            raw += '\n' + self.config.spaces
        
        # Preserve original formatting if description came from existing docstring
        if self.has_existing_description:
            raw += self._with_space(self.description).rstrip() + '\n'
        else:
            raw += self._with_space(self.description).strip() + '\n'
        
        if raw.count(self.config.quotes) == 1:
            raw += self.config.spaces + self.config.quotes
        
        return raw.rstrip()
    
    def _build_description_with_sections(self, desc):
        """Build the description part when sections are present.
        
        :param desc: description text
        :return: description section string
        """
        result = ''
        
        # When there are sections (parameters/arguments), always put description on a new line
        result += '\n' + self.config.spaces
        # Preserve original formatting if description came from existing docstring
        if self.has_existing_description:
            # Preserve original line breaks and formatting
            result += self._with_space(self.description).rstrip() + '\n'
        else:
            result += self._with_space(self.description).strip() + '\n'
        
        return result
    
    def _build_additional_sections(self):
        """Build post and doctests sections.
        
        :return: formatted post and doctests sections
        """
        result = ''
        
        if self.post:
            result += self.config.spaces + self._with_space(self.post).strip() + '\n'
        
        if self.doctests:
            result += self.config.spaces + self._with_space(self.doctests).strip() + '\n'
        
        return result
    
    def _close_docstring(self, raw):
        """Close the docstring with quotes if needed.
        
        :param raw: current docstring content
        :return: docstring with closing quotes
        """
        if raw.count(self.config.quotes) == 1:
            raw += self.config.spaces + self.config.quotes
        return raw.rstrip()
        
    def build(self):
        """Build and return the complete docstring.
        
        :return: complete docstring string
        """
        sep = self.config.docs_tools.get_sep(target='out')
        sep = sep + ' ' if sep != ' ' else sep
        
        raw = self._build_docstring_start()
        desc = self.description.strip()
        has_sections = self._has_sections()
        
        # Handle docstrings without sections
        if not has_sections:
            # Preserve existing description formatting - don't collapse multi-line descriptions
            if desc and desc.count('\n') and not self.has_existing_description:
                desc = ' '.join(desc.split())
            
            if not desc or not desc.count('\n'):
                # Single-line docstring without parameters
                return self._build_single_line_docstring(desc)
            else:
                # Multi-line description without parameters: use multi-line format
                return self._build_multi_line_description_only(desc)
        
        # Handle docstrings with sections
        raw += self._build_description_with_sections(desc)
        
        # Build sections
        raw += self._build_params_section(sep)
        raw += self._build_return_section(sep)
        raw += self._build_raises_section(sep)
        
        # Add post and doctests
        raw += self._build_additional_sections()
        
        return self._close_docstring(raw)

