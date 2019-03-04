#!/usr/bin/env python
# -*- coding: utf-8 -*-

import kwidgin, codecs, opster, configparser, os, sys, random
from kwidgin import Prefs, template

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
    kwidgin.directory_to_xml(output, directory)

@opster.command(usage = '[options...] exam_config_file output_directory')
def genexam(config_file,
            output_dir,
            num_permutations=('n', 10, 'Number of permutations to generate'),
            num_columns=('c', 2, 'Number of columns on paper'),
            run_latex=('r', False, 'Call LaTeX to produce the PDF'),
            view_pdf=('v', False, 'Run LaTeX and show the PDF')):
    """Generate an exam as a directory with LaTeX files"""
    
    config = configparser.RawConfigParser()
    with codecs.open(config_file, 'r', 'utf-8') as infile:
        config.readfp(infile)
    kwidgin.generate_exam_dir(config, output_dir, num_permutations, num_columns)
    if run_latex or view_pdf:
        print("Running LaTeX...")
        absdir = os.path.abspath(output_dir)
        print(absdir)
        ret = os.system("make -j8 -C " + output_dir)
        if ret == 0:
            print("Success!")
            if view_pdf:
                viewer = Prefs.view_pdf_program
                os.system(viewer + " " + output_dir + "/alls.pdf")
        else:
            print("Something went wrong")

@opster.command(usage = '[options...] question_file')
def gen(question_file,
        output_file=('o', '-', 'Output file'),
        seed=('s', 0, 'Seed')):
    """Generate a question from a template file"""
    if seed != 0:
        random.seed(seed)
    infile = sys.stdin
    if question_file != "-":
        infile = open(question_file, 'r')
    question_text = infile.read()
    t = template.Template(question_text, question_file)
    outfile = sys.stdout
    if output_file != '-':
        outfile = open(output_file, 'w')
    sys.path.append(os.path.dirname(question_file))
    outfile.write(t.generate())
    sys.path.pop()
    infile.close()
    outfile.close()

@opster.command(usage = '[options...] rst_file')
def json(rst_file,
         output_file=('o', '-', 'Output file')):
    infile = sys.stdin
    if rst_file != '-':
        infile = open(rst_file, 'r') 
        
    rst_text = infile.read()
    q = kwidgin.render(rst_text, "html")
    random.shuffle(q['answers'])

    outfile = sys.stdout
    if output_file != '-':
        outfile = open(output_file, 'w')

    solutions = ''
    for ch, answer in zip("abcdefghij", q['answers']):
        solutions += ch if answer[0] else ''

    import json
    outfile.write(json.dumps({
       'Question': q['question'].encode('utf-8'),
       'Answers': [a[1] for a in q['answers']],
       'Solution': solutions,
    }))
    outfile.close()
    infile.close()

if __name__ == '__main__':
    opster.dispatch()
