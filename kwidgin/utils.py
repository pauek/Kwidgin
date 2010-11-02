# -*- encoding: utf-8 -*-
# Utilidades para las preguntas

import random

letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def count_true(bitvector):
    return reduce(lambda x, y: x + (0, 1)[y], bitvector)

def flip_coin():
   return random.choice([True, False])

class Lists:
    VariableTypes  = ['int', 'char', 'string', 'float', 'double', 'bool']
    FunctionTypes  = VariableTypes + ['void']
    VariableNames  = ['a', 'b', 'c', 'x', 'y', 'z', 'w', 't', 's']
    AttributeNames = ['mes', 'dia', 'nparaules', 'cont', 'taula', 'data', 'size'
                      'x', 'y', 'z', 'a', 'b', 'c', ]
    MethodNames    = ['es_primer', 'getTitle', 'size', 'push_back', 
                      'getX', 'getY', 'getZ', 'isEmpty', 'isActive', 'isClosed',
                      'numElements', 'setX', 'setY', 'setZ', 'setState',
                      'llegeix', 'escriu', 'reset', 'output', 'input', 
                      'write', 'read', 'onMouseOver', 'onMouseMove',
                      'paintEvent', 'mouseMoveEvent', 'onLayout', 'isScrolling',
                      'scrollTo', 'scrollBy', 'first', 'second', 'third', 'last',
                      'pop', 'push', 'push_front', 'pop_back', 'pop_front', 'count',
                      'rotate', 'move', 'draw', 'remove', 'isIndexed', 'isDirty',
                      'translate', 'scale']
    AbstractClassNames = ['Vector', 'Visim', 'Scal', 'Patrat', 'Filint', 'Lwamb',
                          'Incopel', 'Amila', 'Farigo', 'Vitrem', 'Salem', 'Fapto',
                          'Argo', 'Letif', 'Motif', 'Liqis', 'Tartan', 'Maygo', 
                          'Weebly', 'Arimac', 'Perfo', 'Libac', 'Polumon', 'Sfelk',
                          'Yepto', 'Tamis', 'Wilou', 'Wefex', 'Wufoo', 'Mujat',
                          'Molib', 'Velta', 'Garma', 'Farli', 'Plim', 'Remigo',
                          'Robhik', 'Wepty', 'Spikla', 'Guarmo', 'Relpix', 'Fenam',
                          'Pical', 'Gefren', 'Celib', 'Hafaik', 'Hamild', 'Helefi',
                          'Lombev']
    ParameterLists = [
      '',
      'istream& i',
      'ostream& o',
      'int n',
      'int a, int b',
      'int a, float x',
      'char c',
      'float x',
      'float x, float y',
      'bool empty',
      'bool b, char c',
      'double x, double y',
      'string s',
      'string s, string r',
      'string s, char c'
    ]

def integer_to_bitvector(n, length):
    v = []
    for i in xrange(length):
        q, r = divmod(n, 2)
        v.append(r == 1)
        n = q
    return v

def bitvector_xor(vec1, vec2):
    return [a != b for a, b in zip(vec1, vec2)]

def bitvector_sample_xor(vec, num_samples):
    nbits = len(vec)
    S = bitvector_random_sample(nbits, num_samples, except_zero = True)
    return [bitvector_xor(vec, v) for v in S]

def bitvector_random_sample(num_bits, num_vectors, except_zero = False):
    N = 2**num_bits
    start = 0
    if except_zero: start = 1
    return [integer_to_bitvector(k, num_bits) 
            for k in random.sample(range(start, N), num_vectors)]

def bitvector_to_text(vec, all_of_them):
    num_true = count_true(vec)
    if num_true == len(vec):
        return all_of_them
    elif num_true == 0:
        return "Cap"
    else:
        good = [letters[i] for i in range(len(vec)) if vec[i]]
        if len(good) == 1:
            return u'Només %s' % good[0]
        else:
            return ', '.join(good[:-1]) + ' i ' + good[-1]

class Struct:
   def __init__(self, **entries): 
      self.__dict__.update(entries)

class BinaryChoiceGenerator(object):
    def __init__(self, num_options, num_answers, all_of_them = "Tots"):
        self.noptions = num_options
        self.nanswers = num_answers
        self.all = all_of_them

    def generate_one(self, truth_value):
        assert false
        
    def generate_all(self, bitvector):
        return [self.generate_one(truth) for truth in bitvector]

    def generate(self):
        # Assume first vector is the correct one
        V = bitvector_random_sample(self.noptions, self.nanswers)
        correct_options = V[0]
        self.answers = [Struct(truth = 'false', text = bitvector_to_text(x, self.all)) 
                        for x in V]
        self.answers[0].truth = 'true'
        self.options = [Struct(letter = c, text = t)
                        for c, t in zip(letters, self.generate_all(V[0]))]
