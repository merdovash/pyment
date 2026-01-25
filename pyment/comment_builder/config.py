# -*- coding: utf-8 -*-


class CommentBuilderConfig(object):
    """Configuration class for building docstring comments.
    
    This class encapsulates all configuration options needed to build
    docstrings, making the API cleaner and more maintainable.
    """
    
    __slots__ = (
        'docs_tools', 'spaces', 'quotes', 'before_lim', 'num_of_spaces',
        'skip_empty', 'first_line', 'trailing_space', 'description_on_new_line'
    )
    
    def __init__(self, docs_tools, spaces='', quotes="'''", before_lim='', 
                 num_of_spaces=4, skip_empty=False, first_line=False, 
                 trailing_space='', description_on_new_line=False):
        """Initialize the configuration.
        
        :param docs_tools: DocsTools instance for style management
        :param spaces: leading whitespaces before the element
        :param quotes: type of quotes to use (' ' ' or " " ")
        :param before_lim: prefix for docstring (e.g., 'r' for r'''...)
        :param num_of_spaces: number of spaces for indentation
        :param skip_empty: skip empty sections if True
        :param first_line: description starts on first line if True
        :param trailing_space: trailing space to insert
        :param description_on_new_line: put description on new line if True
        """
        self.docs_tools = docs_tools
        self.spaces = spaces
        self.quotes = quotes
        self.before_lim = before_lim
        self.num_of_spaces = num_of_spaces
        self.skip_empty = skip_empty
        self.first_line = first_line
        self.trailing_space = trailing_space
        self.description_on_new_line = description_on_new_line

