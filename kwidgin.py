#!/usr/bin/env python

import os, codecs
from docutils.core import publish_string
from docutils.parsers import rst
from docutils.nodes import list_item

class answer(list_item):
    def __init__(self, t_or_f):
        self.true_or_false = t_or_f
        list_item.__init__(self)
    
def truefalse(argument):
    return rst.directives.choice(argument, ('false', 'true'))

class AnswerDirective(rst.Directive):
    required_arguments = 1
    optional_arguments = 0
    option_spec = { 'true_or_false': truefalse }
    has_content = True

    def run(self):
        self.assert_has_content()
        args = self.arguments
        if args[0] != 'true' and args[0] != 'false':
            raise self.error("Argument must be `true' or `false'")
        node = answer(args[0] == 'true')
        self.state.nested_parse(self.content, self.content_offset, node)
        return [node]

rst.directives.register_directive('answer', AnswerDirective)

import moodlexml

def file2text(filename):
    f = open(sys.argv[1],'r')
    text = f.read()
    f.close()
    return text

def publish_question(text):
    return publish_string(text, writer = moodlexml.Writer())

def question_to_xml(out, q):
    out.write(u'<question type="multichoice">')
    out.write(u'<name><text>%s</text></name>' % q['title'])
    out.write(u'<questiontext format="html">')
    out.write(u'<text><![CDATA[%s]]></text>' % q['body'])
    out.write(u'</questiontext>')
    out.write(u'<defaultgrade>1</defaultgrade>')
    out.write(u'<shuffleanswers>1</shuffleanswers>')
    out.write(u'<answernumbering>none</answernumbering>')
    for a in q['answers']:
        fr = 0
        if a[0]: fr = 100
        out.write(u'<answer fraction="%d">' % fr)
        out.write(u'<text><![CDATA[%s]]></text>' % a[1])
        out.write(u'</answer>')
    out.write(u'</question>')

def directory_to_xml(out, topdir):
    for root, dirs, files in os.walk(topdir):
        for f in files:
            print join(root, f)

def qlist_to_xml(out, qlist):
    out.write(u'<quiz>')
    for q in qlist:
        question_to_xml(out, q)
    out.write(u'</quiz>')

if __name__ == '__main__':
    import sys
    # dic = publish_question(file2text(sys.argv[1]))
    # for k, v in dic.iteritems():
    #    print k, v
    # out = codecs.open("quiz.xml", 'w', 'utf8')
    # qlist_to_xml(out, [dic])
    directory_to_xml(sys.stdout, sys.argv[1])
    # print publish_string(file2text(sys.argv[1]))
    
    
