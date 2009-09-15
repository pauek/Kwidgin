
import docutils
from docutils import nodes, writers
from docutils.transforms import Transform
import kwidgin

class FlattenAnswers(Transform):

    default_priority = 900

    def apply(self):
        for node in self.document.traverse(kwidgin.answer):
            if len(node) == 1 and isinstance(node[0], nodes.paragraph):
                para = node[0]
                new_ans = kwidgin.answer(node.true_or_false)
                for item in para:
                    new_ans += item
                node.replace_self(new_ans)

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

def encode(text):
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
        self.target.append(encode(node.astext()))

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
    
    def visit_enumerated_list(self, node):
        style = {
            'arabic': 'decimal',
            'loweralpha': 'lower-alpha',
            'upperalpha': 'upper-alpha',
            'lowerroman': 'lower-roman',
            'upperroman': 'upper-roman'
            }
        typ = node['enumtype']
        self.target.append('<ol style="list-style-type: %s">' % style[typ])

    def depart_enumerated_list(self, node):
        self.target.append('</ol>')

    def visit_list_item(self, node):
        self.target.append('<li>')

    def depart_list_item(self, node):
        self.target.append('</li>')
