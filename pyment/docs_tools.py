import dataclasses
import re
from collections import defaultdict

from pyment.domain import ParamsConfig
from pyment.utils import isin_alone, isin_start, isin, get_leading_spaces, RAISES_NAME_REGEX


@dataclasses.dataclass(slots=True)
class ParsedElement:
    nature: str
    name: str


class DocToolsBase(object):
    """

    """

    def __init__(self,
                 first_line=None,
                 optional_sections=None,
                 excluded_sections=None,
                 opt=None,
                 section_headers=None,
                 ):
        """

        :param first_line: indicate if description should start
          on first or second line. By default it will follow global config.
        :type first_line: boolean
        :param optional_sections: list of sections that are not mandatory
          if empty. See subclasses for further description.
        :type optional_sections: list
        :param excluded_sections: list of sections that are excluded,
          even if mandatory. The list is the same as for optional sections.
        :type excluded_sections: list
        :param opt:
        :type opt:
        :param section_headers:
        :type section_headers:
        """
        self.first_line = first_line
        self.optional_sections = list(optional_sections)
        self.excluded_sections = list(excluded_sections)
        self.opt = opt
        self.section_headers = section_headers

    def __iter__(self):
        return self.opt.__iter__()

    def __getitem__(self, key):
        return self.opt[key]

    def get_optional_sections(self):
        """Get optional sections"""
        return self.optional_sections

    def get_excluded_sections(self):
        """Get excluded sections"""
        return self.excluded_sections

    def get_mandatory_sections(self):
        """Get mandatory sections"""
        return [s for s in self.opt
                if s not in self.optional_sections and
                   s not in self.excluded_sections]

    def _get_list_key(self, spaces, lines):
        """ Parse lines and extract the list of key elements.

        :param spaces: leading spaces of starting line
        :type spaces: str
        :param lines: list of strings
        :type lines: list(str)
        :return: list of key elements
        """
        raise NotImplementedError

    def get_list_key(self, data, key, header_lines=1):
        """Get the list of a key elements.
        Each element is a tuple (key=None, description, type=None).
        Note that the tuple's element can differ depending on the key.

        :param data: the data to proceed
        :param key: the key

        """
        data = data.splitlines()
        init = self.get_section_key_line(data, key)
        if init == -1:
            return []
        start, end = self.get_next_section_lines(data[init:])
        # get the spacing of line with key
        spaces = get_leading_spaces(data[init + start])
        start += init + header_lines
        if end != -1:
            end += init
        else:
            end = len(data)

        return self._get_list_key(spaces, data[start:end])

    def get_raise_list(self, data):
        """Get the list of exceptions.
        The list contains tuples (name, desc)

        :param data: the data to proceed

        """
        return_list = []
        lst = self.get_list_key(data, 'raise')
        for l in lst:
            # assume raises are only a name and a description
            name, desc, _ = l
            return_list.append((name, desc))

        return return_list

    def get_return_list(self, data):
        """Get the list of returned values.
        The list contains tuples (name=None, desc, type=None)

        :param data: the data to proceed

        """
        return_list = []
        lst = self.get_list_key(data, 'return')
        for l in lst:
            name, desc, rtype = l
            if l[2] is None:
                rtype = l[0]
                name = None
                desc = desc.strip()
            return_list.append((name, desc, rtype))

        return return_list

    def get_param_list(self, data):
        """Get the list of parameters.
        The list contains tuples (name, desc, type=None)

        :param data: the data to proceed

        """
        return self.get_list_key(data, 'param')

    def get_next_section_start_line(self, data):
        """Get the starting line number of next section.
        It will return -1 if no section was found.
        The section is a section key (e.g. 'Parameters:')
        then the content

        :param data: a list of strings containing the docstring's lines
        :returns: the index of next section else -1
        """
        raise NotImplementedError

    def get_next_section_lines(self, data):
        """Get the starting line number and the ending line number of next section.
        It will return (-1, -1) if no section was found.
        The section is a section key (e.g. 'Parameters') then the content
        The ending line number is the line after the end of the section or -1 if
        the section is at the end.

        :param data: the data to proceed

        """
        end = -1
        start = self.get_next_section_start_line(data)
        if start != -1:
            end = self.get_next_section_start_line(data[start + 1:])
        return start, end

    def get_key_section_header(self, key, spaces):
        """Get the key of the section header

        :param key: the key name
        :param spaces: spaces to set at the beginning of the header

        """
        if key in self.section_headers:
            header = self.section_headers[key]
        else:
            return ''

        return header

    def get_section_key_line(self, data, key, opt_extension=''):
        """Get the next section line for a given key.

        :param data: the data to proceed
        :param key: the key
        :param opt_extension: an optional extension to delimit the opt value

        """
        start = 0
        init = 0
        while start != -1:
            start = self.get_next_section_start_line(data[init:])
            init += start
            if start != -1:
                if data[init].strip().lower() == self.opt[key] + opt_extension:
                    break
                init += 1
        if start != -1:
            start = init
        return start


class NumpydocTools(DocToolsBase):
    """ """

    def __init__(self,
                 first_line=None,
                 optional_sections=('raise', 'also', 'ref', 'note', 'other', 'example', 'method', 'attr'),
                 excluded_sections=()):
        '''
        :param first_line: indicate if description should start
          on first or second line. By default it will follow global config.
        :type first_line: boolean
        :param optional_sections: list of sections that are not mandatory
          if empty. The accepted sections are:
          -param
          -return
          -raise
          -also
          -ref
          -note
          -other
          -example
          -method
          -attr
        :type optional_sections: list
        :param excluded_sections: list of sections that are excluded,
          even if mandatory. The list is the same than for optional sections.
        :type excluded_sections: list

        '''
        super(NumpydocTools, self).__init__(first_line=first_line,
                                            optional_sections=optional_sections,
                                            excluded_sections=excluded_sections,
                                            opt={
                                                'also': 'see also',
                                                'attr': 'attributes',
                                                'example': 'examples',
                                                'method': 'methods',
                                                'note': 'notes',
                                                'other': 'other parameters',
                                                'param': 'parameters',
                                                'raise': 'raises',
                                                'ref': 'references',
                                                'return': 'returns',
                                            },
                                            section_headers={
                                                'param': 'Parameters',
                                                'return': 'Returns',
                                                'raise': 'Raises',
                                            },
                                            )

        self.keywords = [
            ':math:',
            '.. math::',
            'see also',
            '.. image::',
        ]

    def get_next_section_start_line(self, data):
        """Get the starting line number of next section.
        It will return -1 if no section was found.
        The section is a section key (e.g. 'Parameters') followed by underline
        (made by -), then the content

        :param data: a list of strings containing the docstring's lines
        :type data: list(str)
        :returns: the index of next section else -1

        """
        start = -1
        for i, line in enumerate(data):
            if start != -1:
                # we found the key so check if this is the underline
                if line.strip() and isin_alone(['-' * len(line.strip())], line):
                    break
                else:
                    start = -1
            if isin_alone(self.opt.values(), line):
                start = i
        return start

    def get_list_key(self, data, key, header_lines=2):
        """Get the list of a key elements.
        Each element is a tuple (key=None, description, type=None).
        Note that the tuple's element can differ depending on the key.

        :param data: the data to proceed
        :param key: the key

        """
        return super(NumpydocTools, self).get_list_key(data, key, header_lines=header_lines)

    def _get_list_key(self, spaces, lines):
        key_list = []
        parse_key = False
        key, desc, ptype = None, '', None

        for line in lines:
            if len(line.strip()) == 0:
                continue
            # on the same column of the key is the key
            curr_spaces = get_leading_spaces(line)
            if len(curr_spaces) == len(spaces):
                if parse_key:
                    key_list.append((key, desc, ptype))
                elems = line.split(':', 1)
                key = elems[0].strip()
                ptype = elems[1].strip() if len(elems) > 1 else None
                desc = ''
                parse_key = True
            else:
                if len(curr_spaces) > len(spaces):
                    line = line.replace(spaces, '', 1)
                if desc:
                    desc += '\n'
                desc += line
        if parse_key:
            key_list.append((key, desc, ptype))

        return key_list

    def get_attr_list(self, data):
        """Get the list of attributes.
        The list contains tuples (name, desc, type=None)

        :param data: the data to proceed

        """
        return self.get_list_key(data, 'attr')

    def get_raw_not_managed(self, data):
        """Get elements not managed. They can be used as is.

        :param data: the data to proceed

        """
        keys = ['also', 'ref', 'note', 'other', 'example', 'method', 'attr']
        elems = [self.opt[k] for k in self.opt if k in keys]
        data = data.splitlines()
        start = 0
        init = 0
        raw = ''
        spaces = None
        while start != -1:
            start, end = self.get_next_section_lines(data[init:])
            if start != -1:
                init += start
                if isin_alone(elems, data[init]) and \
                        not isin_alone([self.opt[e] for e in self.excluded_sections], data[init]):
                    spaces = get_leading_spaces(data[init])
                    if end != -1:
                        section = [d.replace(spaces, '', 1).rstrip() for d in data[init:init + end]]
                    else:
                        section = [d.replace(spaces, '', 1).rstrip() for d in data[init:]]
                    raw += '\n'.join(section) + '\n'
                init += 2
        return raw

    def get_key_section_header(self, key, spaces):
        """Get the key of the header section

        :param key: the key name
        :param spaces: spaces to set at the beginning of the header

        """
        header = super(NumpydocTools, self).get_key_section_header(key, spaces)
        header = spaces + header + '\n' + spaces + '-' * len(header) + '\n'
        return header


class GoogledocTools(DocToolsBase):
    """ """
    def __init__(self,
                 first_line=None,
                 optional_sections=('raise'),
                 excluded_sections=()):
        """
        :param first_line: indicate if description should start
          on first or second line. By default it will follow global config.
        :type first_line: boolean
        :param optional_sections: list of sections that are not mandatory
          if empty. The accepted sections are:
          -param
          -return
          -raise
        :type optional_sections: list
        :param excluded_sections: list of sections that are excluded,
          even if mandatory. The list is the same than for optional sections.
        :type excluded_sections: list

        """
        super(GoogledocTools, self).__init__(first_line=first_line,
                                             optional_sections=optional_sections,
                                             excluded_sections=excluded_sections,
                                             opt={
                                                 'attr': 'attributes',
                                                 'param': 'args',
                                                 'raise': 'raises',
                                                 'return': 'returns',
                                                 'yield': 'yields',
                                             },
                                             section_headers={
                                                 'param': 'Args',
                                                 'return': 'Returns',
                                                 'raise': 'Raises',
                                             },
                                             )

    def get_section_key_line(self, data, key, opt_extension=':'):
        """Get the next section line for a given key.

        :param data: the data to proceed
        :param key: the key
        :param opt_extension: an optional extension to delimit the opt value

        """
        return super(GoogledocTools, self).get_section_key_line(data, key, opt_extension)

    def _get_list_key(self, spaces, lines):
        key_list = []
        parse_key = False
        key, desc, ptype = None, '', None
        param_spaces = 0

        for line in lines:
            if len(line.strip()) == 0:
                continue
            curr_spaces = get_leading_spaces(line)
            if not param_spaces:
                param_spaces = len(curr_spaces)
            if len(curr_spaces) == param_spaces:
                if parse_key:
                    key_list.append((key, desc, ptype))
                if ':' in line:
                    elems = line.split(':', 1)
                    ptype = None
                    key = elems[0].strip()
                    # the param's type is near the key in parenthesis
                    if '(' in key and ')' in key:
                        tstart = key.index('(') + 1
                        tend = key.index(')')
                        # the 'optional' keyword can follow the style after a comma
                        if ',' in key:
                            tend = key.index(',')
                        ptype = key[tstart:tend].strip()
                        key = key[:tstart - 1].strip()
                    desc = elems[1].strip()
                    parse_key = True
                else:
                    if len(curr_spaces) > len(spaces):
                        line = line.replace(spaces, '', 1)
                    if desc:
                        desc += '\n'
                    desc += line
            else:
                if len(curr_spaces) > len(spaces):
                    line = line.replace(spaces, '', 1)
                if desc:
                    desc += '\n'
                desc += line
        if parse_key or desc:
            key_list.append((key, desc, ptype))

        return key_list

    def get_next_section_start_line(self, data):
        """Get the starting line number of next section.
        It will return -1 if no section was found.
        The section is a section key (e.g. 'Parameters:')
        then the content

        :param data: a list of strings containing the docstring's lines
        :returns: the index of next section else -1

        """
        start = -1
        for i, line in enumerate(data):
            if isin_alone([k + ":" for k in self.opt.values()], line):
                start = i
                break
        return start

    def get_key_section_header(self, key, spaces):
        """Get the key of the section header

        :param key: the key name
        :param spaces: spaces to set at the beginning of the header

        """
        header = super(GoogledocTools, self).get_key_section_header(key, spaces)
        header = spaces + header + ':' + '\n'
        return header


class DocsTools(object):
    """This class provides the tools to manage several types of docstring.
    Currently the following are managed:
    - 'javadoc': javadoc style
    - 'reST': restructured text style compatible with Sphinx
    - 'groups': parameters on beginning of lines (like Google Docs)
    - 'google': the numpy format for docstrings (using an external module)
    - 'numpydoc': the numpy format for docstrings (using an external module)

    """
    # TODO: enhance style dependent separation
    # TODO: add set methods to generate style specific outputs
    # TODO: manage C style (\param)
    def __init__(self, style_in='javadoc', style_out='reST', params=None):
        """Choose the kind of docstring type.

        :param style_in: docstring input style ('javadoc', 'reST', 'groups', 'numpydoc', 'google')
        :type style_in: string
        :param style_out: docstring output style ('javadoc', 'reST', 'groups', 'numpydoc', 'google')
        :type style_out: string
        :param params: if known the parameters names that should be found in the docstring.
        :type params: list

        """
        self.style = {'in': style_in,
                      'out': style_out}
        self.opt = {}
        self.tagstyles = []
        self._set_available_styles()
        self.params: list[ParamsConfig] = params
        self.numpydoc = NumpydocTools()
        self.googledoc = GoogledocTools()

    def _set_available_styles(self):
        """Set the internal styles list and available options in a structure as following:

            param: javadoc: name = '@param'
                            sep  = ':'
                   reST:    name = ':param'
                            sep  = ':'
                   ...
            type:  javadoc: name = '@type'
                            sep  = ':'
                   ...
            ...

        And sets the internal groups style:
            param:  'params', 'args', 'parameters', 'arguments'
            return: 'returns', 'return'
            raise:  'raises', 'raise', 'exceptions', 'exception'

        """
        options_tagstyle = {'keys': ['param', 'type', 'returns', 'return', 'rtype', 'raise'],
                            'styles': {'javadoc': ('@', ':'),  # tuple:  key prefix, separator
                                       'reST': (':', ':'),
                                       'cstyle': ('\\', ' ')}
                           }
        self.tagstyles = list(options_tagstyle['styles'].keys())
        for op in options_tagstyle['keys']:
            self.opt[op] = {}
            for style in options_tagstyle['styles']:
                self.opt[op][style] = {'name': options_tagstyle['styles'][style][0] + op,
                                       'sep': options_tagstyle['styles'][style][1]
                                      }
        self.opt['return']['reST']['name'] = ':returns'
        self.opt['raise']['reST']['name'] = ':raises'
        self.groups = {
                    'param': ['params', 'args', 'parameters', 'arguments'],
                    'return': ['returns', 'return'],
                    'raise': ['raises', 'exceptions', 'raise', 'exception']
                    }

    def autodetect_style(self, data):
        """Determine the style of a docstring,
        and sets it as the default input one for the instance.

        :param data: the docstring's data to recognize.
        :type data: str
        :returns: the style detected else 'unknown'
        :rtype: str

        """
        # evaluate styles with keys

        found_keys = defaultdict(int)
        for style in self.tagstyles:
            for key in self.opt:
                found_keys[style] += data.count(self.opt[key][style]['name'])
        fkey = max(found_keys, key=found_keys.get)
        detected_style = fkey if found_keys[fkey] else 'unknown'

        # evaluate styles with groups

        if detected_style == 'unknown':
            found_groups = 0
            found_googledoc = 0
            found_numpydoc = 0
            found_numpydocsep = 0
            for line in data.strip().splitlines():
                for key in self.groups:
                    found_groups += 1 if isin_start(self.groups[key], line) else 0
                for key in self.googledoc:
                    found_googledoc += 1 if isin_start(self.googledoc[key], line) else 0
                for key in self.numpydoc:
                    found_numpydoc += 1 if isin_start(self.numpydoc[key], line) else 0
                if line.strip() and isin_alone(['-' * len(line.strip())], line):
                    found_numpydocsep += 1
                elif isin(self.numpydoc.keywords, line):
                    found_numpydoc += 1
            # TODO: check if not necessary to have > 1??
            if found_numpydoc and found_numpydocsep:
                detected_style = 'numpydoc'
            elif found_googledoc >= found_groups:
                detected_style = 'google'
            elif found_groups:
                detected_style = 'groups'
        self.style['in'] = detected_style

        return detected_style

    def set_input_style(self, style):
        """Set the input docstring style

        :param style: style to set for input docstring
        :type style: str

        """
        self.style['in'] = style

    def _get_options(self, style):
        """Get the list of keywords for a particular style

        :param style: the style that the keywords are wanted

        """
        return [self.opt[o][style]['name'] for o in self.opt]

    def get_key(self, key, target='in'):
        """Get the name of a key in current style.
        e.g.: in javadoc style, the returned key for 'param' is '@param'

        :param key: the key wanted (param, type, return, rtype,..)
        :param target: the target docstring is 'in' for the input or
          'out' for the output to generate. (Default value = 'in')

        """
        target = 'out' if target == 'out' else 'in'
        return self.opt[key][self.style[target]]['name']

    def get_sep(self, key='param', target='in'):
        """Get the separator of current style.
        e.g.: in reST and javadoc style, it is ":"

        :param key: the key which separator is wanted (param, type, return, rtype,..) (Default value = 'param')
        :param target: the target docstring is 'in' for the input or
          'out' for the output to generate. (Default value = 'in')

        """
        target = 'out' if target == 'out' else 'in'
        if self.style[target] in ['numpydoc', 'google']:
            return ''
        return self.opt[key][self.style[target]]['sep']

    def set_known_parameters(self, params):
        """Set known parameters names.

        :param params: the docstring parameters names
        :type params: list

        """
        self.params = params

    def get_doctests_indexes(self, data):
        """Extract Doctests if found and return it

        :param data: string to parse
        :return: index of start and index of end of the doctest, else (-1, -1)
        :rtype: tuple

        """
        start, end = -1, -1
        datalst = data.splitlines()
        for i, line in enumerate(datalst):
            if start > -1:
                if line.strip() == "":
                    break
                end = i
            elif line.strip().startswith(">>>"):
                start = i
                end = i
        return start, end

    def get_group_key_line(self, data, key):
        """Get the next group-style key's line number.

        :param data: string to parse
        :param key: the key category
        :returns: the found line number else -1

        """
        idx = -1
        for i, line in enumerate(data.splitlines()):
            if isin_start(self.groups[key], line):
                idx = i
        return idx
#        search = '\s*(%s)' % '|'.join(self.groups[key])
#        m = re.match(search, data.lower())
#        if m:
#            key_param = m.group(1)

    def get_group_key_index(self, data, key):
        """Get the next groups style's starting line index for a key

        :param data: string to parse
        :param key: the key category
        :returns: the index if found else -1

        """
        idx = -1
        li = self.get_group_key_line(data, key)
        if li != -1:
            idx = 0
            for line in data.splitlines()[:li]:
                idx += len(line) + len('\n')
        return idx

    def get_group_line(self, data):
        """Get the next group-style key's line.

        :param data: the data to proceed
        :returns: the line number

        """
        idx = -1
        for key in self.groups:
            i = self.get_group_key_line(data, key)
            if (i < idx and i != -1) or idx == -1:
                idx = i
        return idx

    def get_group_index(self, data):
        """Get the next groups style's starting line index

        :param data: string to parse
        :returns: the index if found else -1

        """
        idx = -1
        li = self.get_group_line(data)
        if li != -1:
            idx = 0
            for line in data.splitlines()[:li]:
                idx += len(line) + len('\n')
        return idx

    def get_key_index(self, data, key, starting=True):
        """Get from a docstring the next option with a given key.

        :param data: string to parse
        :param starting: does the key element must start the line (Default value = True)
        :type starting: boolean
        :param key: the key category. Can be 'param', 'type', 'return', ...
        :returns: index of found element else -1
        :rtype: integer

        """
        key = self.opt[key][self.style['in']]['name']
        if key.startswith(':returns'):
            data = data.replace(':return:', ':returns:')  # see issue no_spec_full_comment
        idx = len(data)
        ini = 0
        loop = True
        if key in data:
            while loop:
                i = data.find(key)
                if i != -1:
                    if starting:
                        if not data[:i].rstrip(' \t').endswith('\n') and len(data[:i].strip()) > 0:
                            ini = i + 1
                            data = data[ini:]
                        else:
                            idx = ini + i
                            loop = False
                    else:
                        idx = ini + i
                        loop = False
                else:
                    loop = False
        if idx == len(data):
            idx = -1
        return idx

    def get_elem_index(self, data, starting=True):
        """Get from a docstring the next option.
        In javadoc style it could be @param, @return, @type,...

        :param data: string to parse
        :param starting: does the key element must start the line (Default value = True)
        :type starting: boolean
        :returns: index of found element else -1
        :rtype: integer

        """
        idx = len(data)
        for opt in self.opt.keys():
            i = self.get_key_index(data, opt, starting)
            if i < idx and i != -1:
                idx = i
        if idx == len(data):
            idx = -1
        return idx

    def get_elem_desc(self, data, key):
        """TODO """

    def get_elem_param(self):
        """TODO """

    def get_raise_indexes(self, data):
        """Get from a docstring the next raise name indexes.
        In javadoc style it is after @raise.

        :param data: string to parse
        :returns: start and end indexes of found element else (-1, -1)
          or else (-2, -2) if try to use params style but no parameters were provided.
          Note: the end index is the index after the last name character
        :rtype: tuple

        """
        start, end = -1, -1
        stl_param = self.opt['raise'][self.style['in']]['name']
        if self.style['in'] in self.tagstyles + ['unknown']:
            idx_p = self.get_key_index(data, 'raise')
            if idx_p >= 0:
                idx_p += len(stl_param)
                m = re.match(RAISES_NAME_REGEX, data[idx_p:].strip())
                if m:
                    param = m.group(1)
                    start = idx_p + data[idx_p:].find(param)
                    end = start + len(param)

        if self.style['in'] in ['groups', 'unknown'] and (start, end) == (-1, -1):
            # search = '\s*(%s)' % '|'.join(self.groups['param'])
            # m = re.match(search, data.lower())
            # if m:
            #    key_param = m.group(1)
            pass

        return start, end

    def get_raise_description_indexes(self, data, prev=None):
        """Get from a docstring the next raise's description.
        In javadoc style it is after @param.

        :param data: string to parse
        :param prev: index after the param element name (Default value = None)
        :returns: start and end indexes of found element else (-1, -1)
        :rtype: tuple

        """
        start, end = -1, -1
        if not prev:
            _, prev = self.get_raise_indexes(data)
        if prev < 0:
            return -1, -1
        m = re.match(r'\W*(\w+)', data[prev:])
        if m:
            first = m.group(1)
            start = data[prev:].find(first)
            if start >= 0:
                start += prev
                if self.style['in'] in self.tagstyles + ['unknown']:
                    end = self.get_elem_index(data[start:])
                    if end >= 0:
                        end += start
                if self.style['in'] in ['params', 'unknown'] and end == -1:
                    p1, _ = self.get_raise_indexes(data[start:])
                    if p1 >= 0:
                        end = p1
                    else:
                        end = len(data)

        return start, end
    
    def __parse_param(self, striped: str, style_param: str, ret: dict[str, dict]):
        current_element = ParsedElement(
            name=None,
            nature='param',
        )
        param_name, param_type, param_description = None, None, None
        line = striped.replace(style_param, '', 1).strip()
        if ':' in line:
            param_part, param_description = line.split(':', 1)
        else:
            print("WARNING: malformed docstring parameter")
            param_part = None
        if param_part is not None:
            res = re.split(r'\s+', param_part.strip())
            if len(res) == 1:
                param_name = res[0].strip()
            elif len(res) == 2:
                param_type, param_name = res[0].strip(), res[1].strip()
            else:
                print("WARNING: malformed docstring parameter")
        if param_name:
            # keep track in case of multiline
            current_element.name = param_name
            if param_name not in ret:
                ret[param_name] = {'type': None, 'type_in_param': None, 'description': None}
            if param_type:
                ret[param_name]['type_in_param'] = param_type
            if param_description:
                ret[param_name]['description'] = param_description.strip()
        else:
            print("WARNING: malformed docstring parameter: unable to extract name")
        
        return current_element
    
    def __parse_param_type(self, striped: str, style_type: str, ret: dict[str, dict]):
        current_element = ParsedElement(
            name=None,
            nature='type',
        )
        line = striped.replace(style_type, '', 1).strip()
        if ':' in line:
            param_name, param_type = line.split(':', 1)
            param_name = param_name.strip()
            param_type = param_type.strip()
        else:
            print("WARNING: malformed docstring parameter")
            param_name = None
            param_type = None
        if param_name:
            # keep track in case of multiline
            current_element.name = param_name
            if param_name not in ret:
                ret[param_name] = {'type': None, 'type_in_param': None, 'description': None}
            if param_type:
                ret[param_name]['type'] = param_type.strip()
        
        return current_element
    
    def _extra_tagstyle_elements(self, data):
        ret = {}
        style_param = self.opt['param'][self.style['in']]['name']
        style_type = self.opt['type'][self.style['in']]['name']
        style_rtype = self.opt['rtype'][self.style['in']]['name']
        # fixme for return and raise, ignore last char as there's an optional 's' at the end and they are not managed in this function
        style_return = self.opt['return'][self.style['in']]['name'][:-1]
        style_raise = self.opt['raise'][self.style['in']]['name'][:-1]
        current_element = None
        for line in data.splitlines():
            # parameter statement
            striped = line.strip()
            if striped.startswith(style_param):
                current_element = self.__parse_param(striped, style_param, ret)
            # type statement
            elif striped.startswith(style_type):
                current_element = self.__parse_param_type(striped, style_type, ret)
            elif striped.startswith(style_raise) or striped.startswith(style_return) or striped.startswith(style_rtype):
                # fixme not managed in this function
                current_element = ParsedElement(
                    nature='raise-return',
                    name=None,
                )
            elif current_element:
                # suppose to be line of a multiline element
                if current_element.nature == 'param':
                    if ret[current_element.name]['description'] is None:
                        ret[current_element.name]['description'] = ''
                    ret[current_element.name]['description'] += f"\n{line}"
                elif current_element.nature == 'type':
                    if ret[current_element.name]['description'] is None:
                        ret[current_element.name]['description'] = ''
                    ret[current_element.name]['description'] += f"\n{line}"
        return ret

    def _extract_not_tagstyle_old_way(self, data):
        ret = {}
        listed = 0
        loop = True
        maxi = 10000  # avoid infinite loop but should never happen
        i = 0
        while loop:
            i += 1
            if i > maxi:
                loop = False
            start, end = self.get_param_indexes(data)
            if start >= 0:
                param = data[start: end]
                desc = ''
                param_end = end
                start, end = self.get_param_description_indexes(data, prev=end)
                if start > 0:
                    desc = data[start: end].strip()
                if end == -1:
                    end = param_end
                ptype = ''
                start, pend = self.get_param_type_indexes(data, name=param, prev=end)
                if start > 0:
                    ptype = data[start: pend].strip()
                if param in ret:
                    print(f"WARNING: unexpected parsing duplication of docstring parameter '{param}'")
                ret[param] = {'type': ptype, 'type_in_param': None, 'description': desc}
                data = data[end:]
                listed += 1
            else:
                loop = False
        if i > maxi:
            print("WARNING: an infinite loop was reached while extracting docstring parameters (>10000). This should never happen!!!")
        return ret

    def extract_elements(self, data) -> dict:
        """Extract parameter name, description and type from docstring"""
        ret = []
        tagstyles = self.tagstyles + ['unknown']
        if self.style['in'] in tagstyles:
            ret = self._extra_tagstyle_elements(data)
        else:
            # fixme enhance management of other styles
            ret = self._extract_not_tagstyle_old_way(data)
        return ret

    def get_param_indexes(self, data):
        """Get from a docstring the next parameter name indexes.
        In javadoc style it is after @param.

        :param data: string to parse
        :returns: start and end indexes of found element else (-1, -1)
          or else (-2, -2) if try to use params style but no parameters were provided.
          Note: the end index is the index after the last name character
        :rtype: tuple

        """
        # TODO: new method to extract an element's name so will be available for @param and @types and other styles (:param, \param)
        start, end = -1, -1
        stl_param = self.opt['param'][self.style['in']]['name']
        if self.style['in'] in self.tagstyles + ['unknown']:
            idx_p = self.get_key_index(data, 'param')
            if idx_p >= 0:
                idx_p += len(stl_param)
                m = re.match(r'^([\w]+)', data[idx_p:].strip())
                if m:
                    param = m.group(1)
                    start = idx_p + data[idx_p:].find(param)
                    end = start + len(param)

        if self.style['in'] in ['groups', 'unknown'] and (start, end) == (-1, -1):
            # search = '\s*(%s)' % '|'.join(self.groups['param'])
            # m = re.match(search, data.lower())
            # if m:
            #    key_param = m.group(1)
            pass

        if self.style['in'] in ['params', 'groups', 'unknown'] and (start, end) == (-1, -1):
            if not self.params:
                return -2, -2
            idx = -1
            param = None
            for p in self.params:
                p = p.param
                i = data.find('\n' + p)
                if i >= 0:
                    if idx == -1 or i < idx:
                        idx = i
                        param = p
            if idx != -1:
                start, end = idx, idx + len(param)
        return start, end

    def get_param_description_indexes(self, data, prev=None):
        """Get from a docstring the next parameter's description.
        In javadoc style it is after @param.

        :param data: string to parse
        :param prev: index after the param element name (Default value = None)
        :returns: start and end indexes of found element else (-1, -1)
        :rtype: tuple

        """
        start, end = -1, -1
        if not prev:
            _, prev = self.get_param_indexes(data)
        if prev < 0:
            return -1, -1
        m = re.match(r'\W*(\w+)', data[prev:])
        if m:
            first = m.group(1)
            start = data[prev:].find(first)
            if start >= 0:
                if '\n' in data[prev:prev+start]:
                    # avoid to get next element as a description
                    return -1, -1
                start += prev
                if self.style['in'] in self.tagstyles + ['unknown']:
                    end = self.get_elem_index(data[start:])
                    if end >= 0:
                        end += start
                if self.style['in'] in ['params', 'unknown'] and end == -1:
                    p1, _ = self.get_param_indexes(data[start:])
                    if p1 >= 0:
                        end = p1
                    else:
                        end = len(data)

        return start, end

    def get_param_type_indexes(self, data, name=None, prev=None):
        """Get from a docstring a parameter type indexes.
        In javadoc style it is after @type.

        :param data: string to parse
        :param name: the name of the parameter (Default value = None)
        :param prev: index after the previous element (param or param's description) (Default value = None)
        :returns: start and end indexes of found element else (-1, -1)
          Note: the end index is the index after the last included character or -1 if
          reached the end
        :rtype: tuple

        """
        start, end = -1, -1
        stl_type = self.opt['type'][self.style['in']]['name']
        if not prev:
            _, prev = self.get_param_description_indexes(data)
        if prev >= 0:
            if self.style['in'] in self.tagstyles + ['unknown']:
                idx = self.get_elem_index(data[prev:])
                if idx >= 0 and data[prev + idx:].startswith(stl_type):
                    idx = prev + idx + len(stl_type)
                    m = re.match(r'\W*(\w+)\W+(\w+)\W*', data[idx:].strip())
                    if m:
                        param = m.group(1).strip()
                        if (name and param == name) or not name:
                            desc = m.group(2)
                            start = data[idx:].find(desc) + idx
                            end = self.get_elem_index(data[start:])
                            if end >= 0:
                                end += start

            if self.style['in'] in ['params', 'unknown'] and (start, end) == (-1, -1):
                # TODO: manage this
                pass

        return start, end

    def get_return_description_indexes(self, data):
        """Get from a docstring the return parameter description indexes.
        In javadoc style it is after @return.

        :param data: string to parse
        :returns: start and end indexes of found element else (-1, -1)
          Note: the end index is the index after the last included character or -1 if
          reached the end
        :rtype: tuple

        """
        start, end = -1, -1
        stl_return = self.opt['return'][self.style['in']]['name']
        if self.style['in'] in self.tagstyles + ['unknown']:
            idx = self.get_key_index(data, 'return')
            idx_abs = idx
            # search starting description
            if idx >= 0:
                # FIXME: take care if a return description starts with <, >, =,...
                m = re.match(r'\W*(\w+)', data[idx_abs + len(stl_return):])
                if m:
                    first = m.group(1)
                    idx = data[idx_abs:].find(first)
                    idx_abs += idx
                    start = idx_abs
                else:
                    idx = -1
            # search the end
            idx = self.get_elem_index(data[idx_abs:])
            if idx > 0:
                idx_abs += idx
                end = idx_abs

        if self.style['in'] in ['params', 'unknown'] and (start, end) == (-1, -1):
            # TODO: manage this
            pass

        return start, end

    def get_return_type_indexes(self, data):
        """Get from a docstring the return parameter type indexes.
        In javadoc style it is after @rtype.

        :param data: string to parse
        :returns: start and end indexes of found element else (-1, -1)
          Note: the end index is the index after the last included character or -1 if
          reached the end
        :rtype: tuple

        """
        start, end = -1, -1
        stl_rtype = self.opt['rtype'][self.style['in']]['name']
        if self.style['in'] in self.tagstyles + ['unknown']:
            dstart, dend = self.get_return_description_indexes(data)
            # search the start
            if dstart >= 0 and dend > 0:
                idx = self.get_elem_index(data[dend:])
                if idx >= 0 and data[dend + idx:].startswith(stl_rtype):
                    idx = dend + idx + len(stl_rtype)
                    m = re.match(r'\W*(\w+)', data[idx:])
                    if m:
                        first = m.group(1)
                        start = data[idx:].find(first) + idx
            # search the end
            idx = self.get_elem_index(data[start:])
            if idx > 0:
                end = idx + start

        if self.style['in'] in ['params', 'unknown'] and (start, end) == (-1, -1):
            # TODO: manage this
            pass

        return start, end
