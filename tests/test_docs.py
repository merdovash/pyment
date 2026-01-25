#!/usr/bin/python
# -*- coding: utf-8 -*-
import unittest
import pyment.docstring as docs

myelem = '    def my_method(self, first, second=None, third="value"):'
mydocs = '''        """This is a description of a method.
        It is on several lines.
        Several styles exists:
            -javadoc,
            -reST,
            -cstyle.
        It uses the javadoc style.

        @param first: the 1st argument.
        with multiple lines
        @type first: str
        @param second: the 2nd argument.
        @return: the result value
        @rtype: int
        @raise KeyError: raises a key error exception
        @raise OtherError: raises an other error exception

        """'''

mygrpdocs = '''
    """
    My desc of groups style.
    On two lines.

    Parameters:
      first: the 1st param
      second: the 2nd param
      third: the 3rd param

    Returns:
      a value in a string

    Raises:
      KeyError: when a key error
      OtherError: when an other error
    """'''

googledocs = '''"""This is a Google style docs.

    Args:
      first(str): this is the first param
      second: this is a second param
      third(str, optional): this is a third param

    Returns:
      This is a description of what is returned

    Raises:
      KeyError: raises an exception
      OtherError: when an other error
"""'''

mygrpdocs2 = '''
    """
    My desc of an other kind 
    of groups style.

    Params:
      first -- the 1st param
      second -- the 2nd param
      third -- the 3rd param

    Returns:
      a value in a string

    Raises:
      KeyError -- when a key error
      OtherError -- when an other error
    """'''

mynumpydocs = '''
    """
    My numpydoc description of a kind 
    of very exhautive numpydoc format docstring.

    Parameters
    ----------
    first : array_like
        the 1st param name `first`
    second :
        the 2nd param
    third : {'value', 'other'}, optional
        the 3rd param, by default 'value'

    Returns
    -------
    string
        a value in a string

    Raises
    ------
    KeyError
        when a key error
    OtherError
        when an other error

    See Also
    --------
    a_func : linked (optional), with things to say
             on several lines
    some blabla

    Note
    ----
    Some informations.

    Some maths also:
    .. math:: f(x) = e^{- x}

    References
    ----------
    Biblio with cited ref [1]_. The ref can be cited in Note section.

    .. [1] Adel Daouzli, Sylvain Saïghi, Michelle Rudolph, Alain Destexhe, 
       Sylvie Renaud: Convergence in an Adaptive Neural Network: 
       The Influence of Noise Inputs Correlation. IWANN (1) 2009: 140-148

    Examples
    --------
    This is example of use
    >>> print "a"
    a

    """'''


def torest(docs):
    docs = docs.replace("@", ":")
    docs = docs.replace(":return", ":returns")
    docs = docs.replace(":raise", ":raises")
    return docs


class DocStringTests(unittest.TestCase):

    def test_detects_google_style_after_extracting_params(self):
        doc = googledocs
        d = docs.DocString(myelem, '    ', doc)
        d._extract_docs_params()
        self.assertEqual('google', d.get_input_style())

    def test_detects_numpydoc_style(self):
        doc = mynumpydocs
        d = docs.DocString(myelem, '    ', doc)
        self.assertEqual('numpydoc', d.get_input_style())

    def test_detects_javadoc_style(self):
        doc = mydocs
        d = docs.DocString(myelem, '    ', doc)
        self.assertEqual('javadoc', d.get_input_style())

    def test_detects_rest_style(self):
        doc = torest(mydocs)
        d = docs.DocString(myelem, '    ', doc)
        self.assertEqual('reST', d.get_input_style())

    def test_detects_groups_style(self):
        doc = mygrpdocs
        d = docs.DocString(myelem, '    ', doc)
        self.assertEqual('groups', d.get_input_style())

    def test_javadoc_and_rest_produce_same_output(self):
        doc = mydocs
        dj = docs.DocString(myelem, '    ')
        dj.parse_docs(doc)
        doc = torest(mydocs)
        dr = docs.DocString(myelem, '    ')
        dr.parse_docs(doc)
        self.assertEqual(dj.get_raw_docs(), dr.get_raw_docs())

    def test_parses_function_element_correctly(self):
        d = docs.DocString(myelem, '    ')
        self.assertEqual('def', d.element['deftype'])
        self.assertEqual('my_method', d.element['name'])
        self.assertEqual(3, len(d.element['params']))
        self.assertTrue(type(d.element['params'][0]['param']) is str)
        self.assertEqual(('third', '"value"'),
                         (d.element['params'][2]['param'], d.element['params'][2]['default']))

    def test_parsed_docs_flag_set_correctly(self):
        doc = mydocs
        # nothing to parse
        d = docs.DocString(myelem, '    ')
        d.parse_docs()
        self.assertFalse(d.parsed_docs)
        # parse docstring given at init
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertTrue(d.parsed_docs)
        # parse docstring given in parsing method
        d = docs.DocString(myelem, '    ')
        d.parse_docs(doc)
        self.assertTrue(d.parsed_docs)

    def test_parses_javadoc_description(self):
        doc = mydocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertTrue(d.docs['in']['desc'].strip().startswith('This '))
        self.assertTrue(d.docs['in']['desc'].strip().endswith('style.'))

    def test_parses_groups_description(self):
        doc = mygrpdocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertTrue(d.docs['in']['desc'].strip().startswith('My '))
        self.assertTrue(d.docs['in']['desc'].strip().endswith('lines.'))
    
    def test_parses_numpydoc_description(self):
        doc = mynumpydocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertTrue(d.docs['in']['desc'].strip().startswith('My numpydoc'))
        self.assertTrue(d.docs['in']['desc'].strip().endswith('format docstring.'))

    def test_parses_google_description(self):
        doc = googledocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertTrue(d.docs['in']['desc'].strip().startswith('This is a Google style docs.'))

    def test_parses_rest_params(self):
        doc = torest(mydocs)
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertEqual(2, len(d.docs['in']['params']))
        self.assertTrue(type(d.docs['in']['params'][1]) is tuple)
        # param's name
        self.assertEqual('second', d.docs['in']['params'][1][0])
        # param's type
        self.assertEqual('str', d.docs['in']['params'][0][2])
        self.assertFalse(d.docs['in']['params'][1][2])
        # param's description
        self.assertTrue(d.docs['in']['params'][0][1].startswith("the 1"))

    def test_parses_google_params(self):
        doc = googledocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertEqual(3, len(d.docs['in']['params']))
        self.assertEqual('first', d.docs['in']['params'][0][0])
        self.assertEqual('str', d.docs['in']['params'][0][2])
        self.assertTrue(d.docs['in']['params'][0][1].startswith('this is the first'))
        self.assertFalse(d.docs['in']['params'][1][2])
        self.assertTrue(d.docs['in']['params'][2][1].startswith('this is a third'))
        self.assertEqual('str', d.docs['in']['params'][2][2])

    def test_parses_groups_params(self):
        doc = mygrpdocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertEqual(3, len(d.docs['in']['params']))
        self.assertEqual('first', d.docs['in']['params'][0][0])
        self.assertTrue(d.docs['in']['params'][0][1].startswith('the 1'))
        self.assertTrue(d.docs['in']['params'][2][1].startswith('the 3rd'))

    def test_parses_groups2_params(self):
        doc = mygrpdocs2
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertEqual(3, len(d.docs['in']['params']))
        self.assertEqual('first', d.docs['in']['params'][0][0])
        self.assertTrue(d.docs['in']['params'][0][1].startswith('the 1'))
        self.assertTrue(d.docs['in']['params'][2][1].startswith('the 3rd'))

    def test_parses_numpydoc_params(self):
        doc = mynumpydocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertEqual(3, len(d.docs['in']['params']))
        self.assertEqual('first', d.docs['in']['params'][0][0])
        self.assertEqual('array_like', d.docs['in']['params'][0][2])
        self.assertTrue(d.docs['in']['params'][0][1].strip().startswith('the 1'))
        self.assertFalse(d.docs['in']['params'][1][2])
        self.assertTrue(d.docs['in']['params'][2][1].strip().endswith("default 'value'"))

    def test_parses_javadoc_raises(self):
        doc = mydocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        d.generate_docs()
        self.assertEqual(2, len(d.docs['in']['raises']))
        self.assertTrue(d.docs['in']['raises'][0][0].startswith('KeyError'))
        self.assertTrue(d.docs['in']['raises'][0][1].startswith('raises a key'))
        self.assertTrue(d.docs['in']['raises'][1][0].startswith('OtherError'))
        self.assertTrue(d.docs['in']['raises'][1][1].startswith('raises an other'))

    def test_parses_google_raises(self):
        doc = googledocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertEqual(2, len(d.docs['in']['raises']))
        self.assertEqual('KeyError', d.docs['in']['raises'][0][0])
        self.assertTrue(d.docs['in']['raises'][0][1].startswith('raises an'))
        self.assertEqual('OtherError', d.docs['in']['raises'][1][0])
        self.assertTrue(d.docs['in']['raises'][1][1].startswith('when an other'))

    def test_parses_groups_raises(self):
        doc = mygrpdocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertEqual(2, len(d.docs['in']['raises']))
        self.assertEqual('KeyError', d.docs['in']['raises'][0][0])
        self.assertTrue(d.docs['in']['raises'][0][1].startswith('when a key'))
        self.assertEqual('OtherError', d.docs['in']['raises'][1][0])
        self.assertTrue(d.docs['in']['raises'][1][1].startswith('when an other'))

    def test_parses_groups2_raises(self):
        doc = mygrpdocs2
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertEqual(2, len(d.docs['in']['raises']))
        self.assertEqual('KeyError', d.docs['in']['raises'][0][0])
        self.assertTrue(d.docs['in']['raises'][0][1].startswith('when a key'))
        self.assertEqual('OtherError', d.docs['in']['raises'][1][0])
        self.assertTrue(d.docs['in']['raises'][1][1].startswith('when an other'))

    def test_parses_numpydoc_raises(self):
        doc = mynumpydocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertEqual(2, len(d.docs['in']['raises']))
        self.assertEqual('KeyError', d.docs['in']['raises'][0][0])
        self.assertTrue(d.docs['in']['raises'][0][1].strip().startswith('when a key'))
        self.assertEqual('OtherError', d.docs['in']['raises'][1][0])
        self.assertTrue(d.docs['in']['raises'][1][1].strip().startswith('when an other'))

    def test_parses_javadoc_return(self):
        doc = mydocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertTrue(d.docs['in']['return'].startswith('the result'))
        self.assertEqual('int', d.docs['in']['rtype'])

    def test_parses_groups_return(self):
        doc = mygrpdocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertEqual('a value in a string', d.docs['in']['return'])

    def test_parses_google_return(self):
        doc = googledocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertEqual('This is a description of what is returned', d.docs['in']['return'][0][1])

    def test_parses_numpydoc_return(self):
        doc = mynumpydocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        self.assertEqual('a value in a string', d.docs['in']['return'][0][1])
        d.set_output_style('numpydoc')

    def test_generates_description_correctly(self):
        doc = mydocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        d.generate_docs()
        self.assertEqual(d.docs['in']['desc'], d.docs['out']['desc'])

    def test_generates_return_correctly(self):
        doc = mydocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        d.generate_docs()
        self.assertTrue(d.docs['out']['return'].startswith('the result'))
        self.assertEqual('int', d.docs['out']['rtype'])

    def test_generates_raises_correctly(self):
        doc = mydocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        d.generate_docs()
        self.assertEqual(2, len(d.docs['out']['raises']))
        self.assertTrue(d.docs['out']['raises'][0][0].startswith('KeyError'))
        self.assertTrue(d.docs['out']['raises'][0][1].startswith('raises a key'))
        self.assertTrue(d.docs['out']['raises'][1][0].startswith('OtherError'))
        self.assertTrue(d.docs['out']['raises'][1][1].startswith('raises an other'))

    def test_generates_params_correctly(self):
        doc = mydocs
        d = docs.DocString(myelem, '    ', doc)
        d.parse_docs()
        d.generate_docs()
        self.assertEqual(3, len(d.docs['out']['params']))
        self.assertTrue(type(d.docs['out']['params'][2]) is tuple)
        self.assertEqual(('third', '', None, '"value"'), d.docs['out']['params'][2])
        # param's description
        self.assertTrue(d.docs['out']['params'][1][1].startswith("the 2"))

    def test_generates_javadoc_type_stubs(self):
        doc = mydocs
        d = docs.DocString(myelem, '    ', doc, type_stub=True)
        d.parse_docs()
        d.generate_docs()
        self.assertTrue(':type second: ' in d.docs['out']['raw'])
        self.assertTrue(':type third: ' in d.docs['out']['raw'])

    def test_generates_google_type_stubs(self):
        doc = googledocs
        d = docs.DocString(myelem, '    ', doc, type_stub=True)
        d.parse_docs()
        d.generate_docs()
        self.assertTrue(':type second: ' in d.docs['out']['raw'])

    def test_generates_groups_type_stubs(self):
        doc = mygrpdocs
        d = docs.DocString(myelem, '    ', doc, type_stub=True)
        d.parse_docs()
        d.generate_docs()
        self.assertTrue(':type first: ' in d.docs['out']['raw'])
        self.assertTrue(':type second: ' in d.docs['out']['raw'])
        self.assertTrue(':type third: ' in d.docs['out']['raw'])

    def test_generates_groups2_type_stubs(self):
        doc = mygrpdocs2
        d = docs.DocString(myelem, '    ', doc, type_stub=True)
        d.parse_docs()
        d.generate_docs()
        self.assertTrue(':type first: ' in d.docs['out']['raw'])
        self.assertTrue(':type second: ' in d.docs['out']['raw'])
        self.assertTrue(':type third: ' in d.docs['out']['raw'])

    def test_generates_numpydoc_type_stubs(self):
        doc = mynumpydocs
        d = docs.DocString(myelem, '    ', doc, type_stub=True)
        d.parse_docs()
        d.generate_docs()
        self.assertTrue(':type second: ' in d.docs['out']['raw'])

    def test_handles_function_with_no_params(self):
        elem = "    def noparam():"
        doc = """        '''the no param docstring
        '''"""
        d = docs.DocString(elem, '    ', doc, input_style='javadoc')
        d.parse_docs()
        d.generate_docs()
        self.assertFalse(d.docs['out']['params'])

    def test_generates_one_line_docstring(self):
        elem = "    def oneline(self):"
        doc = """        '''the one line docstring
        '''"""
        d = docs.DocString(elem, '    ', doc, input_style='javadoc')
        d.parse_docs()
        d.generate_docs()
        #print(d.docs['out']['raw'])
        self.assertFalse(d.docs['out']['raw'].count('\n'))


def main():
    unittest.main()

if __name__ == '__main__':
    main()

