#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, codecs, os.path
import escape, template, opster, random, string, hashlib
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

## Translators

class BaseTranslator(nodes.NodeVisitor):
    def __init__(self, document):
        nodes.NodeVisitor.__init__(self, document)
        # self.settings = document.settings
        self.parts = {}
        self.parts['answers'] = []
        self.scratch = []
        self.title = self.last = None
        self.target = self.parts['question'] = []
        
    def put(self, s):
        self.target.append(s)

    def visit_document(self, node):
        self.parts['title'] = node.get('title', '')

    def depart_document(self, node):
        self.parts['question'] = u''.join(self.parts['question'])

    def visit_answer(self, node):
        self.last = self.target
        self.target = self.scratch

    def depart_answer(self, node):
        answ = (node.true_or_false, u''.join(self.scratch))
        self.parts['answers'].append(answ)
        self.scratch = []
        self.target = self.last
    
class MoodleXMLTranslator(BaseTranslator):

    def visit_Text(self, node):
        txt = node.astext().encode('utf-8')
        esc = escape.xhtml_escape(txt)
        self.put(esc.decode('utf-8'))

    def depart_Text(self, node): pass

    def visit_question(self, node): pass
    def depart_question(self, node): pass

    def visit_paragraph(self, node):  self.put('<p>')
    def depart_paragraph(self, node): self.put('</p>')

    def visit_literal_block(self, node):
        style = 'font-family: monospace; font-size: 120%; margin-left: 1.6em'
        self.put('<p style="%s">' % style)

    def depart_literal_block(self, node):
        self.put('</p>')

    def visit_emphasis(self, node):  self.put('<em>')
    def depart_emphasis(self, node): self.put('</em>')

    def visit_literal(self, node):
        self.put('<span style="font-family: monospace; font-size: 120%">')
    
    def depart_literal(self, node):
        self.put('</span>')

    enumerated_style = {
        'arabic': 'decimal',
        'loweralpha': 'lower-alpha',
        'upperalpha': 'upper-alpha',
        'lowerroman': 'lower-roman',
        'upperroman': 'upper-roman'
        }

    def visit_enumerated_list(self, node):
        typ = node['enumtype']
        self.put(u'<ol style="list-style-type: %s">' 
                           % self.enumerated_style[typ])

    def depart_enumerated_list(self, node):
        self.put(u'</ol>')

    def visit_list_item(self, node):  self.put('<li>')
    def depart_list_item(self, node): self.put('</li>')

class LaTeXTranslator(BaseTranslator):

    def visit_question(self, node): 
        self.put("\\begin{pregunta}\n")
        
    def depart_question(self, node):
        self.put("\\end{pregunta}\n")

    def visit_Text(self, node):
        self.put(node.astext())

    def depart_Text(self, node): pass

    def visit_paragraph(self, node): pass
    def depart_paragraph(self, node):
        self.put('\n\n')

    def visit_literal_block(self, node):
        self.put('\\vspace{-.4em}\n\\begin{Verbatim}\n')

    def depart_literal_block(self, node):
        self.put('\n\\end{Verbatim}\n\\vspace{-.4em}')

    def visit_emphasis(self, node):
        self.put('\\emph{')

    def depart_emphasis(self, node):
        self.put('}')

    def visit_literal(self, node):
        if '|' in node.astext():
            self.put('\\Verb@')
        else:
            self.put('\\Verb|')
    
    def depart_literal(self, node):
        if '|' in node.astext():
            self.put('@')
        else:
            self.put('|')

    def visit_answer(self, node):
        BaseTranslator.visit_answer(self, node)
        if node.true_or_false:
            self.put('\\vertadera{')
        else:
            self.put('\\falsa{')

    def depart_answer(self, node):
        self.put('}\n')
        BaseTranslator.depart_answer(self, node)
    
    enumerated_style = {
        'arabic':     '1',
        'loweralpha': 'a',
        'upperalpha': 'A',
        'lowerroman': 'i',
        'upperroman': 'I'
        }

    def visit_enumerated_list(self, node):
        typ = node['enumtype']
        self.put('\\begin{enumerate}[%s.]\n'
                           % self.enumerated_style[typ])
        self.put('\\addtolength{\\itemsep}{-\parskip}\n')
        self.put('\\setlength{\\itemindent}{1em}\n')

    def depart_enumerated_list(self, node):
        self.put('\\end{enumerate}\n')

    def visit_list_item(self, node):
        self.put('\item ')

    def depart_list_item(self, node): pass

## Writers

class QuestionWriter(writers.Writer):
    translator_class = None
    transforms = []

    def __init__(self):
        writers.Writer.__init__(self)
        self.translator = None

    def get_transforms(self):
        return writers.Writer.get_transforms(self) + self.transforms

    def translate(self):
        self.translator = self.translator_class(self.document)
        self.document.walkabout(self.translator)
        self.output = self.parts

    def assemble_parts(self):
        writers.Writer.assemble_parts(self)
        self.parts = self.translator.parts

class MoodleXMLWriter(QuestionWriter):
    translator_class = MoodleXMLTranslator
    transforms = [FlattenAnswers]

class LaTeXWriter(QuestionWriter):
    translator_class = LaTeXTranslator
    transforms = [ShuffleAnswers, FlattenAnswers]

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
    out.write(u'<text><![CDATA[%s]]></text>' % q['question'])
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
            dic = core.publish_parts(txt, writer = MoodleXMLWriter())
            question_to_xml(out, dic)
        for t in t_rsts:
            path = os.path.relpath(t, topdir)
            prefix, _ = os.path.splitext(path)
            category_to_xml(out, prefix)
            templ = template.Template(_file2string(t).encode('utf-8'), 
                                      os.path.basename(t))
            for i in xrange(Prefs.num_permutations):
                text = templ.generate()
                dic = core.publish_parts(text, writer = MoodleXMLWriter())
                dic['title'] += u' (permutació %d)' % i
                question_to_xml(out, dic)
    out.write(u'</quiz>')

## Genexam (LaTeX publisher)

def generate_exam(permutation, config, templ_list, basename):
    cfg = {}
    for x in ('assignatura', 'especialitat', 'temps', 'titol'):
        cfg[x] = config.get(u'exàmen', x)
    
    solutions = ""
    indices = range(len(templ_list))
    random.shuffle(indices)
    with codecs.open('tex/' + basename + '.tex', 'w', 'utf-8') as o:
        o.write("%%%% Permutacio: %d\n" % permutation)
        solucio = ""
        if Prefs.show_answers:
            solucio = "-solucio"
        o.write("\\documentclass{test-fi%s}\n\n" % solucio)
        o.write("\\begin{document}")
        o.write("\\Permutacio{%d}" % permutation)
        o.write("\\Assignatura{%s}" % cfg['assignatura'])
        o.write("\\Especialitat{%s}" % cfg['especialitat'])
        o.write("\\TempsMaxim{%s}" % cfg['temps'])
        o.write("\\Titol{%s}" % cfg['titol'])
        o.write("\\NumPreguntes{%d}\n" % len(templ_list))
        o.write("\\capsalera\n\n")
        o.write("\\begin{multicols*}{2}\n")
        for i in indices:
            t = templ_list[i]
            print permutation, t.name
            q = core.publish_parts(t.generate(), writer = LaTeXWriter())
            o.write(q['question'])
            random.shuffle(q['answers'])
            for a in q['answers']: o.write(a[1])
            t_or_f = [a[0] for a in q['answers']]
            solutions += ['a', 'b', 'c', 'd', 'e', 'f'][t_or_f.index(True)]
        print solutions
        o.write("\\end{multicols*}\n")
        o.write("\\end{document}\n")

    return solutions, indices

Makefile_text = """
PDF=${pdflist}

%.pdf: tex/%.tex
\tlatex $$<  2> /dev/null > /dev/null

enunciat.pdf: $${PDF}
\tpdftk $${PDF} cat output enunciat.pdf
\trm -f $${PDF} *.aux *.log

all: enunciat.pdf

view: all
\tgnome-open enunciat.pdf

clean:
\trm -f $${PDF} *.aux *.log enunciat.pdf
"""

def explode_directories(root, filelist):
    """ Substitute directories with all the files within them """
    _filelist = []
    for f in filelist:
        rf = os.path.join(root, f)
        if os.path.isdir(rf):
            for _root, _, files in os.walk(rf):
                for f in files:
                    if (f[-1] != "~"):
                        _filelist.append(os.path.join(_root, f))
        else:
            _filelist.append(rf)
    return _filelist

def generate_exam_dir(config, output_dir, num_exams):
    # Create directories
    if not os.path.isdir(output_dir): os.mkdir(output_dir)
    os.chdir(output_dir)
    if not os.path.isdir('tex'): os.mkdir('tex')

    # Read questions
    templs = []
    root = config.get('preguntes', 'root')
    filelist = config.get('preguntes', 'list').split('\n')
    filelist = explode_directories(root, filelist)
    with codecs.open('questions.inf', 'w', 'utf-8') as o:
        for k, f in enumerate(filelist):
            fname = f.encode('utf-8')
            text = _file2string(fname).encode('utf-8')
            templ = template.Template(text, fname)
            templs.append(templ)
            sha1 = hashlib.sha1(text).hexdigest()
            o.write("%d;%s;%s\n" % (k, sha1, f))
    lastdir = os.getcwd()

    # Write each exam
    pdflist = ""
    with open('exams.inf', 'w') as o:
        for n in xrange(num_exams):
            prefix = 'exam_%04d' % n
            pdflist += prefix + '.pdf '
            solutions, indices = generate_exam(n, config, templs, prefix)
            o.write("%d;%s;%s\n" % (n, solutions, repr(indices)))

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
                                  'Number of permutations to generate for templates')):
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
