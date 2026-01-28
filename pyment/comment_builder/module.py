# -*- coding: utf-8 -*-

from .builder import CommentBuilder


class ModuleCommentBuilder(CommentBuilder):
    """Builder for module docstrings."""
    
    __slots__ = ()  # Inherits all slots from CommentBuilder
