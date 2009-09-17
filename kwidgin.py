#!/usr/bin/env python

import os, codecs, os.path
from docutils import core, nodes, writers
from docutils.parsers import rst
from docutils.transforms import Transform

## Docutils nodes and directives

def truefalse(argument):
    return rst.directives.choice(argument, ('false', 'true'))

class answer(nodes.list_item):
    def __init__(self, t_or_f):
        self.true_or_false = t_or_f
        nodes.list_item.__init__(self)

class AnswerDirective(rst.Directive):
    required_arguments = 1
    optional_arguments = 0
    has_content = True

    def run(self):
        self.assert_has_content()
        args = self.arguments
        if args[0] not in ('true', 'false'):
            raise self.error("Argument must be `true' or `false'")
        node = answer(args[0] == 'true')
        self.state.nested_parse(self.content, self.content_offset, node)
        return [node]

rst.directives.register_directive('answer', AnswerDirective)

## Transforms

class FlattenAnswers(Transform):
    default_priority = 900

    def apply(self):
        for node in self.document.traverse(answer):
            if len(node) == 1 and isinstance(node[0], nodes.paragraph):
                para = node[0]
                new_ans = answer(node.true_or_false)
                for item in para:
                    new_ans += item
                node.replace_self(new_ans)

## MoodleXML Writer

def _encode(text):
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace('"', "&quot;")
    text = text.replace(">", "&gt;")
    text = text.replace("@", "&#64;")
    return text

class MoodleTranslator(nodes.NodeVisitor):
    def __init__(self, document):
        nodes.NodeVisitor.__init__(self, document)
        self.settings = document.settings
        self.body = []
        self.answers = []
        self.scratch = []
        self.target = None
        self.last = None

    def visit_document(self, node):
        self.target = self.body
        self.title = node.get('title', '')

    def depart_document(self, node): pass

    def visit_Text(self, node):
        self.target.append(_encode(node.astext()))

    def depart_Text(self, node): pass

    def visit_paragraph(self, node):
        self.target.append('<p>')

    def depart_paragraph(self, node):
        self.target.append('</p>')

    def visit_literal(self, node):
        self.target.append('<span style="font-family: monospace; font-size: 120%">')
    
    def depart_literal(self, node):
        self.target.append('</span>')

    def visit_answer(self, node):
        self.last = self.target
        self.target = self.scratch

    def depart_answer(self, node):
        self.answers.append( (node.true_or_false, ''.join(self.scratch)) )
        self.scratch = []
        self.target = self.last
    
    enumerated_style = {
        'arabic': 'decimal',
        'loweralpha': 'lower-alpha',
        'upperalpha': 'upper-alpha',
        'lowerroman': 'lower-roman',
        'upperroman': 'upper-roman'
        }

    def visit_enumerated_list(self, node):
        typ = node['enumtype']
        self.target.append('<ol style="list-style-type: %s">' 
                           % self.enumerated_style[typ])

    def depart_enumerated_list(self, node):
        self.target.append('</ol>')

    def visit_list_item(self, node):
        self.target.append('<li>')

    def depart_list_item(self, node):
        self.target.append('</li>')

class Writer(writers.Writer):
    def __init__(self):
        writers.Writer.__init__(self)
        self.translator = None

    def get_transforms(self):
        return writers.Writer.get_transforms(self) + [FlattenAnswers]

    def translate(self):
        self.translator = MoodleTranslator(self.document)
        self.document.walkabout(self.translator)
        self.output = self.parts

    def assemble_parts(self):
        writers.Writer.assemble_parts(self)
        self.parts['title'] = self.translator.title
        self.parts['body'] = ''.join(self.translator.body)
        self.parts['answers'] = self.translator.answers

## publisher

def file2string(filename):
    f = open(filename,'r')
    text = f.read()
    f.close()
    return text

def publish_question(text):
    return core.publish_string(text, writer = Writer())

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

def category_to_xml(out, name):
    out.write(u'<question type="category">')
    out.write(u'<category><text>%s</text></category>' % name)
    out.write(u'</question>')

def directory_to_xml(out, topdir):
    out.write(u'<quiz>')
    for root, dirs, files in os.walk(topdir):
        count = 0
        rsts = []
        rel = os.path.relpath(root, topdir)
        for f in files:
            name, ext = os.path.splitext(f)
            if ext == ".rst":
                print os.path.join(rel, f)
                rsts.append(os.path.join(root, f))
                count += 1
        if count > 0:
            category_to_xml(out, rel)
        for r in rsts:
            dic = publish_question(file2string(r))
            question_to_xml(out, dic)
    out.write(u'</quiz>')

if __name__ == '__main__':
    import sys
    _, directory, outfile = sys.argv
    output = codecs.open(outfile, 'w', 'utf8')
    directory_to_xml(output, directory)
    
    
