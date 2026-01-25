# -*- coding: utf-8 -*-

from .builder import CommentBuilder


class ModuleCommentBuilder(CommentBuilder):
    """Builder for module docstrings."""
    
    __slots__ = ()  # Inherits all slots from CommentBuilder
    
    def __init__(self, config, strategy):
        """Initialize module comment builder.
        
        :param config: CommentBuilderConfig instance
        :param strategy: CommentFormatStrategy instance
        """
        super(ModuleCommentBuilder, self).__init__(config, strategy)

