
from nose.tools import assert_equal
from KafNafParserPy import KafNafParser
import os, sys
from subprocess import Popen, PIPE


__here__ = os.path.dirname(os.path.realpath(__file__))

os.environ['ALPINO_HOME'] = '/home/izquierdo/tools/Alpino'

def _test_file(this_file):
    input_fd = open(this_file)
    
    cmd = [os.path.join(__here__),'run_parser.sh']
    parser = Popen(os.path.join(__here__,'run_parser.sh'), stdin=input_fd, stdout=PIPE, stderr=PIPE, shell=True)
    return_code = parser.wait()
    
    my_obj = KafNafParser(parser.stdout)
       
    
    #Check the terms
    terms = [term for term in my_obj.get_terms()]
    assert_equal(len(terms),12)
    assert_equal(my_obj.get_term('t_4').get_lemma(),'mooi')
    assert_equal(my_obj.get_term('t_4').get_pos(),'adj')
    
    
    #Check constituents
    trees = [tree for tree in my_obj.get_trees()]
    assert_equal(len(trees),2)
    assert_equal(trees[0].get_terminals_as_list()[1].get_span().get_span_ids(),['t_1'])
    
    #Check dependencies
    dependencies = [dep for dep in my_obj.get_dependencies()]
    assert_equal(len(dependencies),10)
    assert_equal(dependencies[5].get_function(),'hd/su')
    
    
def test_morphosyn_kaf():
    kaf_file = os.path.join(__here__,'examples','file1.in.kaf')
    _test_file(kaf_file)
    
    
def test_morphosyn_naf():
    naf_file = os.path.join(__here__,'examples','file1.in.naf')
    _test_file(naf_file)
   