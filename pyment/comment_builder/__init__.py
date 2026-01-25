# -*- coding: utf-8 -*-

from .config import CommentBuilderConfig
from .builder import CommentBuilder
from .function import FunctionCommentBuilder
from .class_ import ClassCommentBuilder
from .module import ModuleCommentBuilder
from .strategy import (
    CommentFormatStrategy,
    NumpydocStrategy,
    GoogleStrategy,
    DefaultStrategy,
    GroupsStrategy,
    create_strategy
)

__all__ = [
    'CommentBuilderConfig',
    'CommentBuilder',
    'FunctionCommentBuilder',
    'ClassCommentBuilder',
    'ModuleCommentBuilder',
    'CommentFormatStrategy',
    'NumpydocStrategy',
    'GoogleStrategy',
    'DefaultStrategy',
    'GroupsStrategy',
    'create_strategy',
]

