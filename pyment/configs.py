import dataclasses
from dataclasses import field

from pyment.docs_tools import DocsTools
from pyment.domain import ParamsConfig


@dataclasses.dataclass(slots=True)
class CommentBuilderConfig:
    """Configuration class for building docstring comments.

    This class encapsulates all configuration options needed to build
    docstrings, making the API cleaner and more maintainable.
    """
    dst: DocsTools = field(default_factory=DocsTools)
    spaces: str = ''
    quotes: str = '"""'
    before_lim: str = ''
    num_of_spaces: int = 4
    skip_empty: bool = False
    first_line: bool = False
    file_comment: bool = False
    trailing_space: str = ''
    description_on_new_line: bool = False
    show_default_value: bool = True
    indent_empty_lines: bool = True
    ignore_private: bool = False
    init2class: bool = False
    type_tags: bool = True
    method_scope: list[str] = field(default_factory=list)
    output_style: str = 'reST'

    def __post_init__(self):
        self.dst.style['out'] = self.output_style


@dataclasses.dataclass(slots=True)
class ReadConfig:
    encoding: str = 'utf-8'


@dataclasses.dataclass(slots=True)
class ActionConfig:
    convert_only: bool = False


@dataclasses.dataclass(slots=True)
class CaseConfig:
    spaces: str = ''
    name: str = ''
    type: str = ''
    params: list[ParamsConfig] = field(default_factory=list)
    rtype: str = ''
    raw: str = ''
    deftype: str = 'def'


