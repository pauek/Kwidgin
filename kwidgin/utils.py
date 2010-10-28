# -*- encoding: utf-8 -*-
# Utilidades para las preguntas

import random

letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def count_true(bitvector):
    return reduce(lambda x, y: x + (0, 1)[y], bitvector)

def integer_to_bitvector(n):
    v = []
    for i in xrange(4):
        q, r = divmod(n, 2)
        v.append(r == 1)
        n = q
    return v

def bitvector_random_sample(num_bits, num_vectors):
    N = 2**num_bits
    return [integer_to_bitvector(k) 
            for k in random.sample(range(0, N), num_vectors)]

def bitvector_to_text(vec):
    num_true = count_true(vec)
    if num_true == len(vec):
        return "Tots"
    elif num_true == 0:
        return "Cap"
    else:
        good = [letters[i] for i in range(len(vec)) if vec[i]]
        if len(good) == 1:
            return u'Només %s' % good[0]
        else:
            return ', '.join(good[:-1]) + ' i ' + good[-1]
    
class BinaryChoiceGenerator(object):
    def __init__(self, num_options, num_answers):
        correct = 0
        vectors = bitvector_random_sample(num_options, num_answers)
        self._answers = [(('false', 'true')[k == correct], vectors[k]) 
                         for k in range(len(vectors))]
        correct_options = self._answers[correct][1]
        self._options = zip(letters, self.generate_all(correct_options))

    def generate_all(bitvector):
        return [generate_one(truth) for truth in bitvector]

    def generate_one(truth_value):
        assert false
        
    def options(self):
        return [{'letter': o[0], 'text': o[1]} for o in self._options]

    def answers(self):
        return [{'truth': a[0], 'text': bitvector_to_text(a[1])} 
                for a in self._answers]
        
