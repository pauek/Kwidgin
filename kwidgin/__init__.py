#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, codecs, os.path
import escape, template, random, string, hashlib, re
import ConfigParser, StringIO
import time
from docutils import core, nodes, writers
from docutils.parsers import rst
from docutils.transforms import Transform
from copy import copy
from math import log, ceil

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

class box(nodes.Inline, nodes.TextElement): pass
class frame(nodes.Inline, nodes.TextElement): pass

_reg = rst.directives.register_directive
_reg('question', QuestionDirective)
_reg('answer',   AnswerDirective)
_reg('pregunta', QuestionDirective)
_reg('resposta', AnswerDirective)
_reg = rst.roles.register_generic_role
_reg('box', box)
_reg('frame', frame)

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

    def visit_comment(self, node):
        raise nodes.SkipNode

    def unknown_visit(self, node):
        print "WARNING: Visiting unknown node %s" % node.__class__.__name__
        raise nodes.SkipNode
    
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

    def visit_system_message(self, node):
        self.put('System Message {')

    def depart_system_message(self, node):
        self.put('}')

    def visit_block_quote(self, node):
        self.put('<blockquote>')

    def depart_block_quote(self, node):
        self.put('</blockquote>\n')

    def visit_literal_block(self, node):
        style  = 'font-family: monospace;'
        style += 'font-size: 120%;'
        style += 'margin-left: 1.6em'
        self.put('<p style="' + style + '">')

        text = node[0]
        text = string.replace(text, ' ', '&nbsp;')
        text = string.replace(text, '\n', '<br />')
        style  = 'background: rgb(128, 128, 128);'
        style += 'padding: .1em .3em;'
        style += 'color: white'
        patt = '<span style="' + style + '">\\1</span>'
        text = re.sub(':box:`([^`]*)`', patt, text)
        self.put(text)
        self.put('</p>')
        raise nodes.SkipNode

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

    def visit_term(self, node):
        pass

    def depart_term(self, node):
        pass

    def visit_definition_list(self, node):
        self.put('<dl>')

    def depart_definition_list(self, node):
        self.put('</dl>')

    def visit_definition_list_item(self, node):
        pass

    def depart_definition_list_item(self, node):
        pass

    def visit_enumerated_list(self, node):
        typ = node['enumtype']
        self.put(u'<ol style="list-style-type: %s">' 
                           % self.enumerated_style[typ])

    def depart_enumerated_list(self, node):
        self.put(u'</ol>')

    def visit_list_item(self, node):  self.put('<li>')
    def depart_list_item(self, node): self.put('</li>')
    
    common_style = [
        'font-family: monospace',
        'font-size: 120%',
        'padding: .1em .3em'
        ]

    def visit_box(self, node):
        style = copy(self.common_style)
        style += ['background: rgb(128, 128, 128)']
        style += ['color: white']
        self.put('<span style="%s">' % '; '.join(style))

    def depart_box(self, node):
        self.put('</span>')

    def visit_frame(self, node):
        style = copy(self.common_style)
        style += ['border: 1px solid black']
        self.put('<span style="%s">' % '; '.join(style))

    def depart_frame(self, node):
        self.put('</span>')

class HtmlTranslator(MoodleXMLTranslator):
    def visit_literal_block(self, node):
        self.put('<pre>')
        text = node[0]
        text = string.replace(text, ' ', '&nbsp;')
        text = string.replace(text, '\n', '<br />')
        patt = '<span class="box">\\1</span>'
        text = re.sub(':box:`([^`]*)`', patt, text)
        self.put(text)
        self.put('</pre>')
        raise nodes.SkipNode

    def visit_literal(self, node):
        self.put('<tt>')
    
    def depart_literal(self, node):
        self.put('</tt>')

    enumerated_style = {
        'arabic': 'decimal',
        'loweralpha': 'lower-alpha',
        'upperalpha': 'upper-alpha',
        'lowerroman': 'lower-roman',
        'upperroman': 'upper-roman'
        }

    def visit_box(self, node):
        self.put(u'<span class="box">')

    def depart_box(self, node):
        self.put(u'</span>')

    def visit_frame(self, node):
        self.put(u'<span class="frame">')

    def depart_frame(self, node):
        self.put(u'</span>')


class LaTeXTranslator(BaseTranslator):

    def visit_question(self, node): 
        self.put("\n\n\\begin{pregunta}\n")
        
    def depart_question(self, node):
        self.put("\\end{pregunta}\n")

    def visit_Text(self, node):
        self.put(node.astext())

    def depart_Text(self, node): pass

    def visit_paragraph(self, node): pass
    def depart_paragraph(self, node):
        self.put('\n\n')

    def visit_literal_block(self, node):
        self.put('\\vspace{-.55em}\n\\begin{Verbatim}[xleftmargin=5mm,commentchar=@,commandchars=\\\\\\#$]\n')
        text = node[0]
        text = re.sub(':box:`([^`]*)`', '\\wog#\\1$', text)
        self.put(text)
        self.put('\n\\end{Verbatim}\n\\vspace{-.55em}\n')
        raise nodes.SkipNode

    # def depart_literal_block(self, node):
    #    self.put('\n\\end{Verbatim}\n\\vspace{-.4em}')

    def visit_emphasis(self, node):
        self.put('\\emph{')

    def depart_emphasis(self, node):
        self.put('}')

    def print_literal(self, node):
        delim = '|'
        if '|' in node.astext(): delim = '@'
        self.put('\\Verb' + delim)
        text = node.astext()
        text = text.replace('&', '\\&')
        text = text.replace('_', '\\_')
        self.put(text)
        self.put(delim)

    def visit_literal(self, node):
        self.print_literal(node)
        raise nodes.SkipNode

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

    def visit_box(self, node):
        self.put('\\wog{')
        self.print_literal(node[0])
        self.put('}')
        raise nodes.SkipNode

    def visit_frame(self, node):
        self.put('\\wox{')
        self.print_literal(node[0])
        self.put('}')
        raise nodes.SkipNode

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

class HtmlWriter(QuestionWriter):
    translator_class = HtmlTranslator
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

def category_to_xml(out, name, permut=''):
    out.write(u'<question type="category">')
    out.write(u'<category><text>%s/%s%s</text></category>' 
              % (Prefs.base_category, name.decode('utf-8'), permut))
    out.write(u'</question>')

def directory_to_xml(out, topdir):
   out.write(u'<quiz>')
   for root, dirs, files in os.walk(topdir):
      count = 0
      t_rsts, rsts = [], []
      relp = os.path.relpath(root, topdir)
      absp = os.path.abspath(root)
      for f in files:
         prefix, ext = os.path.splitext(f)
         if ext == ".rst":
            print os.path.join(relp, f)
            rsts.append(os.path.join(absp, f))
         elif ext == '.trst':
            print os.path.join(relp, f)
            t_rsts.append(os.path.join(absp, f))
         count += 1
                  
      if count > 0 and relp != ".":
         category_to_xml(out, relp)
      for r in rsts:
         txt = _file2string(r)
         try:
            dic = core.publish_parts(txt, writer = MoodleXMLWriter())
            question_to_xml(out, dic)
         except Exception as e:
            print txt
            raise
              
      for t in t_rsts:
         path = os.path.relpath(t, topdir)
         prefix, _ = os.path.splitext(path)
         category_to_xml(out, prefix, ' [PERMUT]')
         templ = template.Template(_file2string(t).encode('utf-8'), 
                                   os.path.basename(t))
         for i in xrange(Prefs.num_permutations):
            # Add to python path the directory of the template
            sys.path.append(os.path.dirname(t))
            text = templ.generate()
            sys.path.pop()
            #
            dic = core.publish_parts(text, writer = MoodleXMLWriter())
            patt = ' [perm. %%0%dd]' % int(ceil(log(Prefs.num_permutations, 10)))
            dic['title'] += patt % i
            question_to_xml(out, dic)
   out.write(u'</quiz>')

## Genexam (LaTeX publisher)

def render(text, writer):
   w = None
   if writer == "latex":
      w = LaTeXWriter()
   elif writer == "moodlexml":
      w = MoodleXMLWriter()
   elif writer == "html":
      w = HtmlWriter()
   return core.publish_parts(text, writer = w)

def generate_exam(permutation, config, templ_list, basename, num_columns):
   cfg = {}
   for x in ('assignatura', 'especialitat', 'temps', 'titol'):
       cfg[x] = config.get('examen', x)
   
   solutions = ""
   indices = range(len(templ_list))
   random.shuffle(indices)
   buf = StringIO.StringIO()

   buf.write("\\begin{document}")
   buf.write("\\Permutacio{%d}" % permutation)
   buf.write("\\Assignatura{%s}" % cfg['assignatura'])
   buf.write("\\Especialitat{%s}" % cfg['especialitat'])
   buf.write("\\TempsMaxim{%s}" % cfg['temps'])
   buf.write("\\Titol{%s}" % cfg['titol'])
   buf.write("\\NumPreguntes{%d}\n" % len(templ_list))
   buf.write("\\capsalera\n\n")
   buf.write("\\begin{multicols*}{%d}\n" % num_columns)
   for i in indices:
      t = templ_list[i]
      while isinstance(t, list):
         t = random.choice(t)
      # print permutation, t.name
      # Add to python path the directory of the template
      sys.path.append(os.path.dirname(t.name))
      q = core.publish_parts(t.generate(), writer = LaTeXWriter())
      sys.path.pop()
      #
      buf.write(q['question'])
      random.shuffle(q['answers'])
      for a in q['answers']: 
         buf.write(a[1])
      t_or_f = [a[0] for a in q['answers']]
      solutions += ['a', 'b', 'c', 'd', 'e', 'f'][t_or_f.index(True)]
   # print solutions
   buf.write("\\end{multicols*}\n")
   buf.write("\\end{document}\n")
   with codecs.open('tex/' + basename + 'n.tex', 'w', 'utf-8') as file:
      file.write("\\documentclass{test-fi}\n")
      file.write(buf.getvalue())
   with codecs.open('tex/' + basename + 's.tex', 'w', 'utf-8') as file:
      file.write("\\documentclass{test-fi-solucio}\n")
      file.write(buf.getvalue())
   return solutions, indices

Makefile_text = """
PDFS=${pdflist}

all: alln.pdf alls.pdf
\t@rm -f *.aux *.log

alln.pdf: $${PDFS}
\t@pdftk ????n.pdf cat output alln.pdf

alls.pdf: $${PDFS}
\t@pdftk ????s.pdf cat output alls.pdf

%.pdf: tex/%.tex
\t@xelatex -halt-on-error $$< 2> /dev/null > /dev/null

view: all
\txdg-open all.pdf

clean:
\trm -f *.pdf *.aux *.log local.cls
"""

Classfile_text = """\NeedsTeXFormat{LaTeX2e}[1995/12/01]
\ProvidesClass{local}
\LoadClass{test-fi}
"""

Classfile_solucio_text = """\NeedsTeXFormat{LaTeX2e}[1995/12/01]
\ProvidesClass{local}
\LoadClass{test-fi-solucio}
"""

def get_template_tree(question_list):
    """ Substitute directories with all the files within them """
    result = []
    for path in question_list:
        if os.path.isdir(path):
            result.append(get_template_tree([os.path.join(path, f) for f in os.listdir(path)]))
        else:
            _, ext = os.path.splitext(path)
            if ext in ['.rst', '.trst']:
                result.append(path)
            else:
                print "Ignoring file %s" % path
    return result

def templatize(x):
   if isinstance(x, list):
      result = []
      for item in x:
         result.append(templatize(item))
      return result
   else:
      fname = x.encode('utf-8')
      text = _file2string(fname).encode('utf-8')
      return template.Template(text, fname)

def print_tree(x, level = 0):
   if isinstance(x, list):
      print " "*level + "::"
      for item in x:
         print_tree(item, level + 3)
   else:
      print " "*level + x

def generation_date():
   t = time.localtime()
   parts = (t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
   return "%04d%02d%02d%02d%02d%02d" % parts

def generate_exam_dir(config, output_dir, num_permutations, num_columns):
    lastdir = os.getcwd()

    # Create directories
    if not os.path.isdir(output_dir): os.mkdir(output_dir)
    os.chdir(output_dir)
    if not os.path.isdir('tex'): os.mkdir('tex')

    # Read questions
    root = os.path.abspath(config.get('preguntes', 'root'))
    question_list = [os.path.join(root, f) for f in config.get('preguntes', 'list').split('\n')]
    file_tree = get_template_tree(question_list)

    # print_tree(file_tree)
    # print

    # with codecs.open('questions.inf', 'w', 'utf-8') as o:
    # for k, f in enumerate(file_tree):
        # fname = f.encode('utf-8')
        # sha1 = hashlib.sha1(text).hexdigest()
        # o.write("%d;%s;%s\n" % (k, sha1, f))
    templates = templatize(file_tree)

    # Write each exam
    pdflist = ""
    with open('solutions.csv', 'w') as o:
        for n in xrange(num_permutations):
            prefix = '%04d' % n
            pdflist += prefix + 'n.pdf '
            pdflist += prefix + 's.pdf '
            solutions, indices = generate_exam(n, config, templates, prefix, num_columns)
            o.write("%d;%s\n" % (n, solutions))

    # Write metadata
    titol = config.get('examen', 'titol')
    assignatura = config.get('examen', 'assignatura')
    especialitat = config.get('examen', 'especialitat')
    temps = config.get('examen', 'temps')
    # data = config.get('examen', 'data')
    with codecs.open('metadata.csv', 'w', 'utf-8') as o:
        o.write('Titol;%s\n' % titol)
        o.write('Assignatura;%s\n' % assignatura)
        o.write('Especialitat;%s\n' % especialitat)
        o.write('Temps;%s\n' % temps)
        o.write('GenDate;%s\n' % generation_date())
        o.write('NumPermutations;%d\n' % num_permutations)

    # Write Makefile
    t = string.Template(Makefile_text)
    with open('Makefile', 'w') as o:
        o.write(t.substitute(pdflist=pdflist))

    with open('normal.cls', 'w') as o:
        o.write(Classfile_text)

    with open('showsol.cls', 'w') as o:
        o.write(Classfile_solucio_text)

    print "Changing to " + lastdir
    os.chdir(lastdir)

class Prefs:
    base_category = 'Kwidgin'
    view_pdf_program = 'xdg-open'
    num_permutations = 5
