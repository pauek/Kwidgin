#!/usr/bin/env python

from docutils.core import publish_string
from docutils.parsers import rst
from docutils.nodes import list_item

class answer(list_item): pass
    
def truefalse(argument):
    return rst.directives.choice(argument, ('false', 'true'))

class AnswerDirective(rst.Directive):
    required_arguments = 1
    optional_arguments = 0
    option_spec = { 'result': truefalse }
    has_content = True

    def run(self):
        self.assert_has_content()
        node = answer()
        self.state.nested_parse(self.content, self.content_offset, node)
        return [node]

rst.directives.register_directive('answer', AnswerDirective)

if __name__ == '__main__':
    import sys
    file = open(sys.argv[1],'r')
    text = file.read()
    file.close()
    print publish_string(text)
    
    
