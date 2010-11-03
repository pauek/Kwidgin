#!/usr/bin/env python
# -*- coding: utf-8 -*-

import kwidgin, codecs, opster, ConfigParser, os
from kwidgin import Prefs

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
            num_exams=('n', 10, 'Number of exams to generate'),
            show_answers=('s', False, 'Show answers in output'),
            run_latex=('r', False, 'Call LaTeX to produce the PDF'),
            view_pdf=('v', False, 'Run LaTeX and show the PDF')):
    """Generate an exam as a directory with LaTeX files"""
    
    config = ConfigParser.RawConfigParser()
    with codecs.open(config_file, 'r', 'utf-8') as infile:
        config.readfp(infile)
    Prefs.show_answers = show_answers
    kwidgin.generate_exam_dir(config, output_dir, num_exams)
    if run_latex or view_pdf:
        print "Running LaTeX..."
        absdir = os.path.abspath(output_dir)
        print absdir
        ret = os.system("make -j8 -C " + output_dir)
        if ret == 0:
            print "Success!"
            if view_pdf:
                viewer = Prefs.view_pdf_program
                os.system(viewer + " " + output_dir + "/enunciat.pdf")
        else:
            print "Something went wrong"

if __name__ == '__main__':
    opster.dispatch()
