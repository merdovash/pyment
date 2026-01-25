# -*- coding: utf-8 -*-

from .builder import CommentBuilder


class ClassCommentBuilder(CommentBuilder):
    """Builder for class docstrings."""
    
    __slots__ = ()  # Inherits all slots from CommentBuilder
    
    def __init__(self, config, strategy):
        """Initialize class comment builder.
        
        :param config: CommentBuilderConfig instance
        :param strategy: CommentFormatStrategy instance
        """
        super(ClassCommentBuilder, self).__init__(config, strategy)
    
    def _should_use_one_line_format_with_spaces(self):
        """For classes, use one-line format with spaces for auto-generated docstrings.
        
        :return: True for classes
        """
        return True

