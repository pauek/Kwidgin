
Kwidgin
-------

Strange name, yeah. It comes from QuizGen, which is impossible to
pronounce. QuizGen: Quiz Generator. With this thing you can write
programs that generate questions, put a lot of them together, and have
them permuted in such a way that it is safe to have students take the
quiz even if they can read each others exam. Pretty useful, huh?

I will admit (if you press hard enough) that this software not yet
ready for prime time...

Ok, how do I use it?
''''''''''''''''''''

You will need Opster (in the latest Ubuntu just type ``apt-get install
python-opster`` or get it from `here
<http://pypi.python.org/pypi/opster>`_).

You have to write a "config file" for an exam::

   [exàmen]
   assignatura = Fonaments d'Informàtica
   especialitat = Grau Audiovisuals
   temps = 10m
   titol = Examen Part I

   [preguntes]
   root = ../demo-questions
   list = Divisio entera i modul.trst
          Equivalencia.trst
          Expressio Booleana.trst

This file is included in the ``demo-questions`` directory as ``config``

Then, from the distribution directory, you can run::

  ./kwidgin.py help genexam

To see the options or if you can't wait::

  ./kwidgin.py genexam -n 10 -s -v demo-questions/config exam

This will generate 10 exams (``-n 10``) using
``demo-questions/config``, will show a black mark for the right
answers (``-s``) and will pop Evince to show you the PDF
(``-v``). Files will be written in the ``exam`` directory.

Some LaTeX classes are needed that are not included here, I will add
them at some point.
