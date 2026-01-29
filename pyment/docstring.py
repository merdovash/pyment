# -*- coding: utf-8 -*-

import re

__author__ = "A. Daouzli"
__copyright__ = "Copyright 2012-2018, A. Daouzli; Copyright 2026, V. Schekochihin"
__licence__ = "GPL3"
__version__ = "0.5.0"
__maintainer__ = "V. Schekochihin"

from dataclasses import fields
from textwrap import dedent
from typing import Generator

from pyment.comment_builder import ClassCommentBuilder, ModuleCommentBuilder, FunctionCommentBuilder, CommentBuilder, \
    create_strategy
from pyment.configs import CommentBuilderConfig, CaseConfig
from pyment.domain import ParamsConfig
from pyment.utils import normalize_default_value, log_function, log_generator

"""
Formats supported at the time:
 - javadoc, reST (restructured text, Sphinx):
 managed  -> description, param, type, return, rtype, raise
 - google:
 managed  -> description, parameters, return, raises
 - numpydoc:
 managed  -> description, parameters, return (first of list only), raises

"""


class DocString(object):
    """This class represents the docstring"""
    
    def __init__(self, elem_raw, comment_config: CommentBuilderConfig, case_config: CaseConfig, spaces='', docs_raw=None, input_style=None,
                 trailing_space=True, type_stub=False, before_lim=''):
        """
        :param elem_raw: raw data of the element (def or class).
        :param spaces: the leading whitespaces before the element
        :param docs_raw: the raw data of the docstring part if any.
        :param style_in: docstring input style ('javadoc', 'reST', 'groups', 'numpydoc', 'google', None).
          If None will be autodetected
        :type style_in: string
        :param style_out: docstring output style ('javadoc', 'reST', 'groups', 'numpydoc', 'google')
        :type style_out: string
        :param trailing_space: if set, a trailing space will be inserted in places where the user
          should write a description
        :type trailing_space: boolean
        :param type_stub: if set, an empty stub will be created for a parameter type
        :type type_stub: boolean
        :param before_lim: specify raw or unicode or format docstring type (ie. "r" for r'''... or "fu" for fu'''...)

        """
        self.comment_config = comment_config
        self.case_config = case_config
        self.before_lim = before_lim
        self.trailing_space = ''
        self.type_stub = type_stub
        if trailing_space:
            self.trailing_space = ' '
        if docs_raw and not input_style:
            self.comment_config.dst.autodetect_style(docs_raw)
        elif input_style:
            self.set_input_style(input_style)
        self.element = case_config
        if docs_raw:
            docs_raw = docs_raw.strip()
            if docs_raw.startswith('"""') or docs_raw.startswith("'''"):
                docs_raw = docs_raw[3:]
            if docs_raw.endswith('"""') or docs_raw.endswith("'''"):
                docs_raw = docs_raw[:-3]
        self.docs = {
            'in': {
                'raw': docs_raw,
                'doctests': "",
                'desc': None,
                'params': [],
                'types': [],
                'return': None,
                'rtype': None,
                'raises': []
                },
            'out': {
                'raw': '',
                'desc': None,
                'params': [],
                'types': [],
                'return': None,
                'rtype': None,
                'raises': [],
                'spaces': spaces + ' ' * 2
                }
            }
        if '\t' in spaces:
            self.docs['out']['spaces'] = spaces + '\t'
        elif (len(spaces) % 4) == 0 or spaces == '':
            # FIXME: should bug if tabs for class or function (as spaces=='')
            self.docs['out']['spaces'] = spaces + ' ' * 4
        self.parsed_elem = False
        self.parsed_docs = False
        self.generated_docs = False
        self._options = {
            'hint_rtype_priority': True,  # priority in type hint else in docstring
            'hint_type_priority': True,  # priority in type hint else in docstring
            'rst_type_in_param_priority': True,  # in reST docstring priority on type present in param else on type
        }

        self.parse_definition()

    def __str__(self):
        # for debugging
        txt = "\n\n** " + str(self.element.name)
        txt += ' of type ' + str(self.element.deftype) + ':'
        txt += str(self.docs['in']['desc']) + '\n'
        txt += '->' + str(self.docs['in']['params']) + '\n'
        txt += '***>>' + str(self.docs['out']['raw']) + '\n' + '\n'
        return txt

    def __repr__(self):
        return f'<{self.__class__.__name__} name={self.case_config.name}>'

    def get_input_docstring(self):
        """Get the input raw docstring.

        :returns: the input docstring if any.
        :rtype: str or None

        """
        return self.docs['in']['raw']

    def get_input_style(self):
        """Get the input docstring style

        :returns: the style for input docstring
        :rtype: style: str

        """
        # TODO: use a getter
        return self.comment_config.dst.style['in']

    def set_input_style(self, style):
        """Sets the input docstring style

        :param style: style to set for input docstring
        :type style: str

        """
        # TODO: use a setter
        self.comment_config.dst.style['in'] = style

    def get_spaces(self):
        """Get the output docstring initial spaces.

        :returns: the spaces

        """
        return self.docs['out']['spaces']

    def set_spaces(self, spaces):
        """Set for output docstring the initial spaces.

        :param spaces: the spaces to set

        """
        self.docs['out']['spaces'] = spaces

    def parse_definition(self, raw=None):
        """Parses the element's elements (type, name and parameters) :)
        e.g.: def methode(param1, param2='default')
        def                      -> type
        methode                  -> name
        param1, param2='default' -> parameters

        :param raw: raw data of the element (def or class). If None will use `self.element['raw']` (Default value = None)

        """
        # TODO: retrieve return from element external code (in parameter)
        if raw is None:
            l = self.element.raw.strip()
        else:
            l = raw.strip()
        is_class = False
        if l.startswith('async def ') or l.startswith('def ') or l.startswith('class '):
            # retrieves the type
            if l.startswith('def'):
                self.element.deftype = 'def'
                l = l.replace('def ', '')
            elif l.startswith('async'):
                self.element.deftype = 'def'
                l = l.replace('async def ', '')
            else:
                self.element.deftype = 'class'
                l = l.replace('class ', '')
                is_class = True
            # retrieves the name
            self.element.name = l[:l.find('(')].strip()
            if not is_class:
                parameters, return_type = self._extract_signature_elements(self._remove_signature_comment(l))
                # remove self and cls parameters if any and also empty params (if no param)
                remove_keys = []
                for params in parameters:
                    if params.param in ['self', 'cls']:
                        remove_keys.append(params)
                    elif not params.param:
                        remove_keys.append(params)
                for key in remove_keys:
                    parameters.remove(key)
                if return_type:
                    self.element.rtype = return_type # TODO manage this
                self.element.params.extend(parameters)
        self.parsed_elem = True

    def _remove_signature_comment(self, txt):
        """If there is a comment at the end of the signature statement, remove it"""
        ret = ""
        inside = None
        end_inside = {'(': ')', '{': '}', '[': ']', "'": "'", '"': '"'}
        for c in txt:
            if (inside and end_inside[inside] != c) or (not inside and c in end_inside.keys()):
                if not inside:
                    inside = c
                ret += c
                continue
            if inside and c == end_inside[inside]:
                inside = None
                ret += c
                continue
            if not inside and c == '#':
                # found a comment so signature is finished we stop parsing
                break
            ret += c
        return ret

    def _extract_signature_elements(self, txt: str) -> tuple[list[ParamsConfig], str]:
        start = txt.find('(') + 1
        end_start = txt.rfind(')')
        end_end = txt.rfind(':')
        return_type = txt[end_start + 1:end_end].replace(' ', '').replace('\t', '').replace('->', '')
        elems: list[ParamsConfig] = []
        elem_idx = 0
        reading = 'param'
        current_param = ParamsConfig()
        elems.append(current_param)
        inside = None
        end_inside = {'(': ')', '{': '}', '[': ']', "'": "'", '"': '"'}
        for c in txt[start:end_start]:
            if (inside and end_inside[inside] != c) or (not inside and c in end_inside.keys()):
                if not inside:
                    inside = c
                if reading == 'type':
                    current_param.type += c
                elif reading == 'default':
                    current_param.default += c
                else:
                    # FIXME: this should not happen!
                    raise Exception("unexpected nested element after "+str(inside)+" while reading "+reading)
                continue
            if inside and c == end_inside[inside]:
                inside = None
            if reading == 'param':
                if c not in ': ,=':
                    current_param.param += c
                else:
                    if c == ' ' and current_param.param or c != ' ':
                        reading = 'after_param'
            elif reading == 'type':
                if c not in ',=':
                    current_param.type += c
                else:
                    reading = 'after_type'
            elif reading == 'default':
                if c != ',':
                    current_param.default += c
                else:
                    reading = 'after_default'
            if reading.startswith('after_'):
                if reading == 'after_param' and c == ':':
                    reading = 'type'
                elif c == ',':
                    elem_idx += 1
                    current_param = ParamsConfig()
                    elems.append(current_param)
                    reading = 'param'
                elif c == '=':
                    reading = 'default'

        # strip extracted elements
        for elem in elems:
            for field in fields(elem):
                value = getattr(elem, field.name, None)
                if value is not None:
                    setattr(elem, field.name, value.strip())
        return elems, return_type.strip()

    def _extract_docs_doctest(self):
        """Extract the doctests if found.
        If there are doctests, they are removed from the input data and set on
        a specific buffer as they won't be altered.

        :return: True if found and proceeded else False
        """
        result = False
        data = self.docs['in']['raw']
        start, end = self.comment_config.dst.get_doctests_indexes(data)
        while start != -1:
            print (start, end)
            result = True
            datalst = data.splitlines()
            if self.docs['in']['doctests'] != "":
                self.docs['in']['doctests'] += '\n'
            self.docs['in']['doctests'] += '\n'.join(datalst[start:end + 1]) + '\n'
            self.docs['in']['raw'] = '\n'.join(datalst[:start] + datalst[end + 1:])
            data = self.docs['in']['raw']
            start, end = self.comment_config.dst.get_doctests_indexes(data)
        if self.docs['in']['doctests'] != "":
            data = '\n'.join([d.rstrip().replace(self.docs['out']['spaces'], '', 1) for d in self.docs['in']['doctests'].splitlines()])
            self.docs['out']['doctests'] = data
        return result
    
    @log_function
    def __extract_current_desc(self):
        # FIXME: the indentation of descriptions is lost
        data = '\n'.join([d.rstrip().replace(self.docs['out']['spaces'], '', 1) for d in self.docs['in']['raw'].splitlines()])
        if self.comment_config.dst.style['in'] == 'groups':
            idx = self.comment_config.dst.get_group_index(data)
        elif self.comment_config.dst.style['in'] == 'google':
            lines = data.splitlines()
            line_num = self.comment_config.dst.googledoc.get_next_section_start_line(lines)
            if line_num == -1:
                idx = -1
            else:
                idx = len('\n'.join(lines[:line_num]))
        elif self.comment_config.dst.style['in'] == 'numpydoc':
            lines = data.splitlines()
            line_num = self.comment_config.dst.numpydoc.get_next_section_start_line(lines)
            if line_num == -1:
                idx = -1
            else:
                idx = len('\n'.join(lines[:line_num]))

        elif self.comment_config.dst.style['in'] == 'unknown':
            idx = -1
        else:
            idx = self.comment_config.dst.get_elem_index(data)
        
        if idx == 0:
            return ''
        elif idx == -1:
            return data
        else:
            return data[:idx]
    
    def _extract_docs_description(self):
        """Extract main description from docstring"""
        self.docs['in']['desc'] = self.__extract_current_desc()

    def _extract_groupstyle_docs_params(self):
        """Extract group style parameters"""
        data = '\n'.join([d.rstrip().replace(self.docs['out']['spaces'], '', 1) for d in self.docs['in']['raw'].splitlines()])
        idx = self.comment_config.dst.get_group_key_line(data, 'param')
        if idx >= 0:
            data = data.splitlines()[idx + 1:]
            end = self.comment_config.dst.get_group_line('\n'.join(data))
            end = end if end != -1 else len(data)
            for i in range(end):
                # FIXME: see how retrieve multiline param description and how get type
                line = data[i]
                param = None
                desc = ''
                ptype = ''
                m = re.match(r'^\W*(\w+)[\W\s]+(\w[\s\w]+)', line.strip())
                if m:
                    param = m.group(1).strip()
                    desc = m.group(2).strip()
                else:
                    m = re.match(r'^\W*(\w+)\W*', line.strip())
                    if m:
                        param = m.group(1).strip()
                if param:
                    self.docs['in']['params'].append((param, desc, ptype))

    def _extract_tagstyle_docs_params(self):
        """ """
        data = '\n'.join([d.rstrip().replace(self.docs['out']['spaces'], '', 1) for d in self.docs['in']['raw'].splitlines()])
        extracted = self.comment_config.dst.extract_elements(data)
        for param_name, param in extracted.items():
            param_type = param['type']
            if self._options['rst_type_in_param_priority'] and param['type_in_param']:
                param_type = param['type_in_param']
            desc = param['description'] if param['description'] else ""
            self.docs['in']['params'].append((param_name, desc, param_type))

    def _old_extract_tagstyle_docs_params(self):
        """ """
        data = '\n'.join([d.rstrip().replace(self.docs['out']['spaces'], '', 1) for d in self.docs['in']['raw'].splitlines()])
        listed = 0
        loop = True
        maxi = 10000  # avoid infinite loop but should never happen
        i = 0
        while loop:
            i += 1
            if i > maxi:
                loop = False
            start, end = self.comment_config.dst.get_param_indexes(data)
            if start >= 0:
                param = data[start: end]
                desc = ''
                param_end = end
                start, end = self.comment_config.dst.get_param_description_indexes(data, prev=end)
                if start > 0:
                    desc = data[start: end].strip()
                if end == -1:
                    end = param_end
                ptype = ''
                start, pend = self.comment_config.dst.get_param_type_indexes(data, name=param, prev=end)
                if start > 0:
                    ptype = data[start: pend].strip()
                # a parameter is stored with: (name, description, type)
                self.docs['in']['params'].append((param, desc, ptype))
                data = data[end:]
                listed += 1
            else:
                loop = False
        if i > maxi:
            print("WARNING: an infinite loop was reached while extracting docstring parameters (>10000). This should never happen!!!")

    def _extract_docs_params(self):
        """Extract parameters description and type from docstring. The internal computed parameters list is
        composed by tuples (parameter, description, type).

        """
        if self.comment_config.dst.style['in'] == 'numpydoc':
            data = '\n'.join([d.rstrip().replace(self.docs['out']['spaces'], '', 1) for d in self.docs['in']['raw'].splitlines()])
            self.docs['in']['params'] += self.comment_config.dst.numpydoc.get_param_list(data)
        elif self.comment_config.dst.style['in'] == 'google':
            data = '\n'.join([d.rstrip().replace(self.docs['out']['spaces'], '', 1) for d in self.docs['in']['raw'].splitlines()])
            self.docs['in']['params'] += self.comment_config.dst.googledoc.get_param_list(data)
        elif self.comment_config.dst.style['in'] == 'groups':
            self._extract_groupstyle_docs_params()
        elif self.comment_config.dst.style['in'] in ['javadoc', 'reST']:
            self._extract_tagstyle_docs_params()

    def _extract_groupstyle_docs_raises(self):
        """ """
        data = '\n'.join([d.rstrip().replace(self.docs['out']['spaces'], '', 1) for d in self.docs['in']['raw'].splitlines()])
        idx = self.comment_config.dst.get_group_key_line(data, 'raise')
        if idx >= 0:
            data = data.splitlines()[idx + 1:]
            end = self.comment_config.dst.get_group_line('\n'.join(data))
            end = end if end != -1 else len(data)
            for i in range(end):
                # FIXME: see how retrieve multiline raise description
                line = data[i]
                param = None
                desc = ''
                m = re.match(r'^\W*([\w.]+)[\W\s]+(\w[\s\w]+)', line.strip())
                if m:
                    param = m.group(1).strip()
                    desc = m.group(2).strip()
                else:
                    m = re.match(r'^\W*(\w+)\W*', line.strip())
                    if m:
                        param = m.group(1).strip()
                if param:
                    self.docs['in']['raises'].append((param, desc))

    def _extract_tagstyle_docs_raises(self):
        """ """
        data = '\n'.join([d.rstrip().replace(self.docs['out']['spaces'], '', 1) for d in self.docs['in']['raw'].splitlines()])
        listed = 0
        loop = True
        maxi = 10000  # avoid infinite loop but should never happen
        i = 0
        while loop:
            i += 1
            if i > maxi:
                loop = False
            start, end = self.comment_config.dst.get_raise_indexes(data)
            if start >= 0:
                param = data[start: end]
                desc = ''
                start, end = self.comment_config.dst.get_raise_description_indexes(data, prev=end)
                if start > 0:
                    desc = data[start: end].strip()
                # a parameter is stored with: (name, description)
                self.docs['in']['raises'].append((param, desc))
                data = data[end:]
                listed += 1
            else:
                loop = False
        if i > maxi:
            print("WARNING: an infinite loop was reached while extracting docstring parameters (>10000). This should never happen!!!")

    def _extract_docs_raises(self):
        """Extract raises description from docstring. The internal computed raises list is
        composed by tuples (raise, description).

        """
        if self.comment_config.dst.style['in'] == 'numpydoc':
            data = '\n'.join([d.rstrip().replace(self.docs['out']['spaces'], '', 1) for d in self.docs['in']['raw'].splitlines()])
            self.docs['in']['raises'] += self.comment_config.dst.numpydoc.get_raise_list(data)
        if self.comment_config.dst.style['in'] == 'google':
            data = '\n'.join([d.rstrip().replace(self.docs['out']['spaces'], '', 1) for d in self.docs['in']['raw'].splitlines()])
            self.docs['in']['raises'] += self.comment_config.dst.googledoc.get_raise_list(data)
        elif self.comment_config.dst.style['in'] == 'groups':
            self._extract_groupstyle_docs_raises()
        elif self.comment_config.dst.style['in'] in ['javadoc', 'reST']:
            self._extract_tagstyle_docs_raises()

    def _extract_groupstyle_docs_return(self):
        """ """
        # TODO: manage rtype
        data = '\n'.join([d.rstrip().replace(self.docs['out']['spaces'], '', 1) for d in self.docs['in']['raw'].splitlines()])
        idx = self.comment_config.dst.get_group_key_line(data, 'return')
        if idx >= 0:
            data = data.splitlines()[idx + 1:]
            end = self.comment_config.dst.get_group_line('\n'.join(data))
            end = end if end != -1 else len(data)
            data = '\n'.join(data[:end]).strip()
            self.docs['in']['return'] = data.rstrip()

    def _extract_tagstyle_docs_return(self):
        """ """
        data = '\n'.join([d.rstrip().replace(self.docs['out']['spaces'], '', 1) for d in self.docs['in']['raw'].splitlines()])
        start, end = self.comment_config.dst.get_return_description_indexes(data)
        if start >= 0:
            if end >= 0:
                self.docs['in']['return'] = data[start:end].rstrip()
            else:
                self.docs['in']['return'] = data[start:].rstrip()
        start, end = self.comment_config.dst.get_return_type_indexes(data)
        if start >= 0:
            if end >= 0:
                self.docs['in']['rtype'] = data[start:end].rstrip()
            else:
                self.docs['in']['rtype'] = data[start:].rstrip()

    def _extract_docs_return(self):
        """Extract return description and type"""
        if self.comment_config.dst.style['in'] == 'numpydoc':
            data = '\n'.join([d.rstrip().replace(self.docs['out']['spaces'], '', 1) for d in self.docs['in']['raw'].splitlines()])
            self.docs['in']['return'] = self.comment_config.dst.numpydoc.get_return_list(data)
            self.docs['in']['rtype'] = None
# TODO: fix this
        elif self.comment_config.dst.style['in'] == 'google':
            data = '\n'.join([d.rstrip().replace(self.docs['out']['spaces'], '', 1) for d in self.docs['in']['raw'].splitlines()])
            self.docs['in']['return'] = self.comment_config.dst.googledoc.get_return_list(data)
            self.docs['in']['rtype'] = None
        elif self.comment_config.dst.style['in'] == 'groups':
            self._extract_groupstyle_docs_return()
        elif self.comment_config.dst.style['in'] in ['javadoc', 'reST']:
            self._extract_tagstyle_docs_return()

    def _extract_docs_other(self):
        """Extract other specific sections"""
        if self.comment_config.dst.style['in'] == 'numpydoc':
            data = '\n'.join([d.rstrip().replace(self.docs['out']['spaces'], '', 1) for d in self.docs['in']['raw'].splitlines()])
            lst = self.comment_config.dst.numpydoc.get_list_key(data, 'also')
            lst = self.comment_config.dst.numpydoc.get_list_key(data, 'ref')
            lst = self.comment_config.dst.numpydoc.get_list_key(data, 'note')
            lst = self.comment_config.dst.numpydoc.get_list_key(data, 'other')
            lst = self.comment_config.dst.numpydoc.get_list_key(data, 'example')
            lst = self.comment_config.dst.numpydoc.get_list_key(data, 'attr')
            # TODO do something with this?

    def parse_docs(self, raw=None, before_lim=''):
        """Parses the docstring

        :param raw: the data to parse if not internally provided (Default value = None)
        :param before_lim: specify raw or unicode or format docstring type (ie. "r" for r'''... or "fu" for fu'''...)

        """
        self.before_lim = before_lim
        if raw is not None:
            raw = raw.strip()
            if raw.startswith('"""') or raw.startswith("'''"):
                raw = raw[3:]
            if raw.endswith('"""') or raw.endswith("'''"):
                raw = raw[:-3]
            self.docs['in']['raw'] = raw
            self.comment_config.dst.autodetect_style(raw)
        if self.docs['in']['raw'] is None:
            return
        self.comment_config.dst.set_known_parameters(self.element.params)
        self._extract_docs_doctest()
        self._extract_docs_params()
        self._extract_docs_return()
        self._extract_docs_raises()
        self._extract_docs_description()
        self._extract_docs_other()
        self.parsed_docs = True
    
    @log_function
    def __extract_desc(self):
        """Extract description"""
        # TODO: manage different in/out styles
        if self.docs['in']['desc']:
            return self.docs['in']['desc']
        return ''

    def _set_desc(self):
        """Sets the global description if any"""
        self.docs['out']['desc'] = self.__extract_desc()

    @log_generator
    def __extract_params(self) -> Generator[tuple[str, str, str | None, str | None], None, None]:
        # TODO: manage different in/out styles
        # convert the list of signature's extracted params into a dict with the names of param as keys
        sig_params = {e.param: {'type': e.type, 'default': e.default} for e in self.element.params}
        # convert the list of docsting's extracted params into a dict with the names of param as keys
        docs_params = {
            name: {
                'description': desc,
                'type': param_type,
            } for name, desc, param_type in self.docs['in']['params']
        }
        for name in sig_params:
            # WARNING: Note that if a param in docstring isn't in the signature params, it will be dropped
            sig_type, sig_default = sig_params[name]['type'], sig_params[name]['default']
            out_description = ""
            out_type = sig_type if sig_type else None
            out_default = sig_default if sig_default else None
            # Normalize default value: convert triple quotes to single quotes
            if out_default:
                out_default = normalize_default_value(out_default)
            if name in docs_params:
                out_description = docs_params[name]['description']
                if not out_type or (not self._options['hint_type_priority'] and docs_params[name]['type']):
                    out_type = docs_params[name]['type']
            yield name, out_description, out_type, out_default
    
    def _set_params(self):
        """Sets the parameters with types, descriptions and default value if any
        taken from the input docstring and the signature parameters"""
        self.docs['out']['params'].extend(self.__extract_params())

    @log_function
    def __extract_raises(self) -> list | None:
        # TODO: manage different in/out styles
        # manage setting if not mandatory for numpy but optional
        if self.docs['in']['raises']:
            if self.comment_config.dst.style['out'] != 'numpydoc' or self.comment_config.dst.style['in'] == 'numpydoc' or \
                    (self.comment_config.dst.style['out'] == 'numpydoc' and
                     'raise' not in self.comment_config.dst.numpydoc.get_excluded_sections()):
                # list of parameters is like: (name, description)
                return list(self.docs['in']['raises'])
    
    def _set_raises(self):
        """Sets the raises and descriptions"""
        raises = self.__extract_raises()
        if raises:
            self.docs['out']['raises'] = raises

    @log_function
    def __extract_return(self) -> tuple[str | None, str | None]:
        # TODO: manage return retrieved from element code (external)
        # TODO: manage different in/out styles
        rtype, rcomment = None, None
        if isinstance(self.docs['in']['return'], list) and self.comment_config.dst.style['out'] not in ('groups', 'numpydoc', 'google'):
            # TODO: manage return names
            # manage not setting return if not mandatory for numpy
            lst = self.docs['in']['return']
            if lst:
                if lst[0][0] is not None:
                    rcomment = "%s-> %s" % (lst[0][0], lst[0][1])
                else:
                    rcomment = lst[0][1]
                rtype = lst[0][2]
        else:
            rcomment = self.docs['in']['return']
            rtype = self.docs['in']['rtype']
        if (self._options['hint_rtype_priority'] or not self.docs['out']['rtype']) and self.element.rtype:
            rtype = self.element.rtype
        
        return rtype, rcomment
    
    def _set_return(self):
        """Sets the return parameter with description and rtype if any"""
        rtype, rcomment = self.__extract_return()
        self.docs['out']['rtype'] = rtype
        self.docs['out']['return'] = rcomment
    
    @log_function
    def __extract_other(self) -> str | None:
        if self.comment_config.dst.style['in'] == 'numpydoc':
            if self.docs['in']['raw'] is not None:
                return self.comment_config.dst.numpydoc.get_raw_not_managed(self.docs['in']['raw'])
            elif 'post' not in self.docs['out'] or self.docs['out']['post'] is None:
                return ''
        return None
        
    def _set_other(self):
        """Sets other specific sections"""
        # manage not setting if not mandatory for numpy
        self.docs['out']['post'] = self.__extract_other()
    
    def _define_builder(self) -> CommentBuilder:
        # Create appropriate builder using the stored config and strategy
        strategy = create_strategy(self.comment_config.dst.style.get('out', 'reST'), self.comment_config, self.case_config)
        
        element_type = self.element.deftype
        if element_type == 'class':
            return ClassCommentBuilder(self.comment_config, self.case_config, strategy)
        if element_type == 'module':
            return ModuleCommentBuilder(self.comment_config, self.case_config, strategy)
        # 'def' or default
        return FunctionCommentBuilder(self.comment_config, self.case_config, strategy)
    
    def _create_builder(self):
        """Create and configure the appropriate builder based on element type.
        
        :return: configured CommentBuilder instance
        """
        # Determine element type
        builder = self._define_builder()
        
        # Set data in builder
        builder.set_name(self.element.name)
        builder.set_description(self.docs['out']['desc'].strip(), has_existing=bool(self.docs['in']['desc'] and self.docs['in']['desc'].strip()))
        builder.set_params(self.docs['out']['params'])
        builder.set_return(self.docs['out']['return'], self.docs['out']['rtype'])
        builder.set_raises(self.docs['out']['raises'])
        builder.set_post(self.docs['out'].get('post', ''))
        builder.set_doctests(self.docs['out'].get('doctests', ''))
        builder.set_element_info(self.docs['in']['raw'])
        
        return builder
    
    def _set_raw(self):
        """Sets the output raw docstring"""
        builder = self._create_builder()
        self.docs['out']['raw'] = builder.build()
    
    @log_function
    def generate_docs(self):
        """Generates the output docstring"""
        self._set_desc()
        self._set_params()
        self._set_return()
        self._set_raises()
        self._set_other()
        self._set_raw()
        self.generated_docs = True
        return True

    def get_raw_docs(self):
        """Generates raw docstring

        :returns: the raw docstring

        """
        if not self.generated_docs:
            self.generate_docs()
        return self.docs['out']['raw']


if __name__ == "__main__":
    help(DocString)
