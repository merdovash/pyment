# -*- coding: utf-8 -*-

from .doctools_base import DocToolsBase
from .utils import isin_alone, get_leading_spaces


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

