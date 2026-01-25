# -*- coding: utf-8 -*-

from .builder import CommentBuilder


class FunctionCommentBuilder(CommentBuilder):
    """Builder for function docstrings."""
    
    __slots__ = ()  # Inherits all slots from CommentBuilder
    
    def __init__(self, config, strategy):
        """Initialize function comment builder.
        
        :param config: CommentBuilderConfig instance
        :param strategy: CommentFormatStrategy instance
        """
        super(FunctionCommentBuilder, self).__init__(config, strategy)
    
    def _format_name_as_description(self, name):
        """Format function name as a description by splitting into words and capitalizing first word.
        
        Examples:
        - hello_world -> "Hello world"
        - calculate_total_sum -> "Calculate total sum"
        - UserAccountManager -> "User account manager"
        - __init__ -> "Initialize"
        - func1 -> "Func1"
        
        :param name: the function name
        :type name: str
        :return: formatted description
        :rtype: str
        """
        if not name:
            return ''
        
        # Handle special methods like __init__, __str__, etc.
        if name.startswith('__') and name.endswith('__'):
            # Remove leading and trailing underscores
            inner = name[2:-2]
            if inner:
                # For __init__, return "Initialize", for others capitalize first letter
                if inner == 'init':
                    return 'Initialize'
                # Capitalize first letter
                return inner[0].upper() + inner[1:].lower()
            return name
        
        # Split on underscores first
        parts = name.split('_')
        
        # For each part, split on camelCase boundaries
        words = []
        for part in parts:
            if not part:
                continue
            
            # Split camelCase: insert space before each capital letter (except the first)
            camel_parts = []
            current_word = ''
            for i, char in enumerate(part):
                if char.isupper() and i > 0 and current_word:
                    # Start a new word
                    camel_parts.append(current_word)
                    current_word = char
                else:
                    current_word += char
            if current_word:
                camel_parts.append(current_word)
            
            words.extend(camel_parts)
        
        if not words:
            return name
        
        # Join words with spaces and capitalize first word
        result = ' '.join(words)
        # Capitalize first letter only
        return result[0].upper() + result[1:].lower() if len(result) > 1 else result.upper()
    
    def set_name(self, name):
        """Set the function name and generate description from it.
        
        :param name: the function name
        :return: self for method chaining
        """
        self.element_name = name
        if name:
            self.description = self._format_name_as_description(name)
        else:
            self.description = ''
        return self

