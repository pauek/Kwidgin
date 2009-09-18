#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, codecs, os.path
import escape, template, opster, random, string
import ConfigParser, cStringIO
from docutils import core, nodes, writers
from docutils.parsers import rst
from docutils.transforms import Transform
from copy import copy

## Docutils nodes and directives

def truefalse(argument):
    return rst.directives.choice(argument, ('false', 'true'))

class answer(nodes.list_item):
    def __init__(self, t_or_f):
        self.true_or_false = t_or_f
        nodes.list_item.__init__(self)

class question(nodes.compound): pass

class QuestionDirective(rst.Directive):
    has_content = True

    def run(self):
        self.assert_has_content()
        node = question()
        self.state.nested_parse(self.content, self.content_offset, node)
        return [node]

class AnswerDirective(rst.Directive):
    has_content = True
    required_arguments = 1

    def run(self):
        self.assert_has_content()
        args = self.arguments
        if args[0] not in ('true', 'false'):
            raise self.error("Argument must be `true' or `false'")
        node = answer(args[0] == 'true')
        self.state.nested_parse(self.content, self.content_offset, node)
        return [node]

_reg = rst.directives.register_directive
_reg('question', QuestionDirective)
_reg('answer',   AnswerDirective)
_reg('pregunta', QuestionDirective)
_reg('resposta', AnswerDirective)

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
        txt = node.astext().encode('utf-8')
        esc = escape.xhtml_escape(txt)
        self.target.append(esc.decode('utf-8'))

    def depart_Text(self, node): pass

    def visit_question(self, node): pass
    def depart_question(self, node): pass

    def visit_paragraph(self, node):
        self.target.append(u'<p>')

    def depart_paragraph(self, node):
        self.target.append(u'</p>')

    def visit_literal_block(self, node):
        style = 'font-family: monospace; font-size: 120%; margin-left: 1.6em'
        self.target.append('<p style="%s">' % style)

    def depart_literal_block(self, node):
        self.target.append('</p>')

    def visit_emphasis(self, node):
        self.target.append(u'<em>')

    def depart_emphasis(self, node):
        self.target.append(u'</em>')

    def visit_literal(self, node):
        self.target.append(u'<span style="font-family: monospace; font-size: 120%">')
    
    def depart_literal(self, node):
        self.target.append(u'</span>')

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
        self.target.append(u'<ol style="list-style-type: %s">' 
                           % self.enumerated_style[typ])

    def depart_enumerated_list(self, node):
        self.target.append(u'</ol>')

    def visit_list_item(self, node):
        self.target.append(u'<li>')

    def depart_list_item(self, node):
        self.target.append(u'</li>')

class MoodleXMLWriter(writers.Writer):
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

## MoodleXML publisher

def _file2string(filename):
    f = codecs.open(filename, 'r', 'utf-8')
    text = f.read()
    f.close()
    return text

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
    out.write(u'<category><text>%s/%s</text></category>' 
              % (Prefs.base_category, name.decode('utf-8')))
    out.write(u'</question>')

def directory_to_xml(out, topdir):
    out.write(u'<quiz>')
    for root, dirs, files in os.walk(topdir):
        count = 0
        t_rsts, rsts = [], []
        rel = os.path.relpath(root, topdir)
        for f in files:
            prefix, ext = os.path.splitext(f)
            if ext == ".rst":
                print os.path.join(rel, f)
                rsts.append(os.path.join(root, f))
                count += 1
            elif ext == '.trst':
                print os.path.join(rel, f)
                t_rsts.append(os.path.join(root, f))
                count += 1
                    
        if count > 0 and rel != ".":
            category_to_xml(out, rel)
        for r in rsts:
            txt = _file2string(r)
            dic = core.publish_string(txt, writer = MoodleXMLWriter())
            question_to_xml(out, dic)
        for t in t_rsts:
            path = os.path.relpath(t, topdir)
            prefix, _ = os.path.splitext(path)
            category_to_xml(out, prefix)
            templ = template.Template(_file2string(t).encode('utf-8'), 
                                      os.path.basename(t))
            for i in xrange(Prefs.num_permutations):
                text = templ.generate()
                dic = core.publish_string(text, writer = MoodleXMLWriter())
                dic['title'] += u' (permutació %d)' % i
                question_to_xml(out, dic)
    out.write(u'</quiz>')

# Genexam

class ShuffleAnswers(Transform):
    default_priority = 910

    def apply(self):
        # Collect answers
        answers = []
        for a in self.document.traverse(answer):
            answers.append(a)
        shuffled = copy(answers)
        random.shuffle(shuffled)
        for a, s in zip(answers, shuffled):
            a.replace_self(s)

class LaTeXWriter(writers.Writer):
    def get_transforms(self):
        added = [FlattenAnswers, ShuffleAnswers]
        return writers.Writer.get_transforms(self) + added

    def translate(self):
        translator = LaTeXTranslator(self.document)
        self.document.walkabout(translator)
        self.output = ''.join(translator.output)

class LaTeXTranslator(nodes.NodeVisitor):
    def __init__(self, document):
        nodes.NodeVisitor.__init__(self, document)
        self.settings = document.settings
        self.answers = []
        self.output = []

    def visit_document(self, node): pass
    def depart_document(self, node): pass

    def visit_question(self, node): 
        self.output.append("\\begin{pregunta}\n")
        
    def depart_question(self, node):
        self.output.append("\\end{pregunta}\n")

    def visit_Text(self, node):
        self.output.append(node.astext())

    def depart_Text(self, node): pass

    def visit_paragraph(self, node): pass
    def depart_paragraph(self, node):
        self.output.append('\n\n')

    def visit_literal_block(self, node):
        self.output.append('\\vspace{-.4em}\n\\begin{Verbatim}\n')

    def depart_literal_block(self, node):
        self.output.append('\n\\end{Verbatim}\n\\vspace{-.4em}')

    def visit_emphasis(self, node):
        self.output.append('\\emph{')

    def depart_emphasis(self, node):
        self.output.append('}')

    def visit_literal(self, node):
        self.output.append('\\Verb|')
    
    def depart_literal(self, node):
        self.output.append('|')

    def visit_answer(self, node):
        if node.true_or_false:
            self.output.append('\\vertadera{')
        else:
            self.output.append('\\falsa{')

    def depart_answer(self, node):
        self.output.append('}\n')
    
    enumerated_style = {
        'arabic':     '1',
        'loweralpha': 'a',
        'upperalpha': 'A',
        'lowerroman': 'i',
        'upperroman': 'I'
        }

    def visit_enumerated_list(self, node):
        typ = node['enumtype']
        self.output.append('\\begin{enumerate}[%s.]\n'
                           % self.enumerated_style[typ])
        self.output.append('\\addtolength{\\itemsep}{-\parskip}\n')
        self.output.append('\\setlength{\\itemindent}{1em}\n')

    def depart_enumerated_list(self, node):
        self.output.append('\\end{enumerate}\n')

    def visit_list_item(self, node):
        self.output.append('\item ')

    def depart_list_item(self, node): pass
    

def generate_exam(permutation, config, templ_list, filename):
    cfg = {}
    for x in ('assignatura', 'especialitat', 'temps', 'titol'):
        cfg[x] = config.get(u'exàmen', x)
    
    with codecs.open(filename, 'w', 'utf-8') as out:
        out.write("%%%% Permutacio: %d\n" % permutation)
        solucio = ""
        if Prefs.show_answers:
            solucio = "-solucio"
        out.write("\\documentclass{test-fi%s}\n\n" % solucio)
        out.write("\\begin{document}")
        out.write("\\Permutacio{%d}" % permutation)
        out.write("\\Assignatura{%s}" % cfg['assignatura'])
        out.write("\\Especialitat{%s}" % cfg['especialitat'])
        out.write("\\TempsMaxim{%s}" % cfg['temps'])
        out.write("\\Titol{%s}" % cfg['titol'])
        out.write("\\NumPreguntes{%d}\n" % len(templ_list))
        out.write("\\capsalera\n\n")
        out.write("\\begin{multicols*}{2}\n")
        lst = copy(templ_list)
        random.shuffle(lst)
        for t in lst:
            print permutation, t.name
            rst = t.generate()
            latex = core.publish_string(rst, writer = LaTeXWriter(),
                                        settings_overrides = {'output_encoding': 'unicode'})
            out.write(latex)
        out.write("\\end{multicols*}\n")
        out.write("\\end{document}\n")

Makefile_text = """
PDF=${pdflist}

%.pdf: tex/%.tex
\tlatex $$<  2> /dev/null > /dev/null

enunciat.pdf: $${PDF}
\tpdftk $${PDF} cat output enunciat.pdf
\trm -f $${PDF} *.aux *.log

all: enunciat.pdf

clean:
\trm -f $${PDF} *.aux *.log enunciat.pdf
"""

def generate_exam_dir(config, output_dir, num_exams):
    templs = []
    root = config.get('preguntes', 'root')
    filelist = config.get('preguntes', 'list').split('\n')
    for f in filelist:
        fname = os.path.join(root, f)
        templ = template.Template(_file2string(fname).encode('utf-8'), 
                                  f.encode('utf-8'))
        templs.append(templ)
    lastdir = os.getcwd()

    # Create directories
    if not os.path.isdir(output_dir): os.mkdir(output_dir)
    os.chdir(output_dir)
    if not os.path.isdir('tex'): os.mkdir('tex')

    # TODO: Fix this
    #
    # Write config (no puedo en UTF-8!!) 
    # with codecs.open('exam.cfg', 'w', 'utf-8') as cfgout:
    #   config.write(cfgout)

    # Write each exam
    pdflist = ""
    for n in xrange(num_exams):
        exam_file = './tex/exam_%04d.tex' % n
        pdflist += 'exam_%04d.pdf ' % n
        generate_exam(n, config, templs, exam_file)

    # Write Makefile
    t = string.Template(Makefile_text)
    with open('Makefile', 'w') as o:
        o.write(t.substitute(pdflist=pdflist))

    os.chdir(lastdir)


# Commands

class Prefs:
    base_category = 'Kwidgin'
    num_permutations = 5
    show_answers = False

@opster.command(usage = '[options...] directory output_file')
def moodlexml(directory,
              outfile,
              base_category = ('b', Prefs.base_category, 
                               'Use this category to contain all others'),
              num_permutations = ('n', Prefs.num_permutations, 
                                  'Number of permutation to use in question templates')):
    """Export a directory with RST and TRST files to the MoodleXML format"""
    Prefs.base_category = base_category
    Prefs.num_permutations = num_permutations
    output = codecs.open(outfile, 'w', 'utf8')
    directory_to_xml(output, directory)

@opster.command(usage = '[options...] exam_config_file output_directory')
def genexam(config_file,
            output_dir,
            num_exams=('n', 10, 'Number of exams to generate'),
            show_answers=('s', False, 'Show answers in output')):
    """Generate an exam as a directory with LaTeX files"""
    
    config = ConfigParser.RawConfigParser()
    with codecs.open(config_file, 'r', 'utf-8') as infile:
        config.readfp(infile)
    Prefs.show_answers = show_answers
    generate_exam_dir(config, output_dir, num_exams)

if __name__ == '__main__':
    opster.dispatch()

