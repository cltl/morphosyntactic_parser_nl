#!/usr/bin/env python

import os
import sys
import tempfile
import shutil
import argparse

from KafNafParserPy import *
from subprocess import Popen,PIPE, check_output
from lxml import etree
from convert_penn_to_kaf import convert_penn_to_knaf_with_numtokens
from alpino_dependency import Calpino_dependency

last_modified='22sept2015'
version="0.2"
this_name = 'Morphosyntactic parser based on Alpino'

###############################################

def set_up_alpino():
    ##Uncomment next line and point it to your local path to Alpino if you dont want to set the environment variable ALPINO_HOME
    #os.environ['ALPINO_HOME'] = '/home/izquierdo/tools/Alpino'

    if 'ALPINO_HOME' not in os.environ:
        print>>sys.stderr,'ALPINO_HOME variable not set. Set this variable to point to your local path to Alpino. For instance:'
        print>>sys.stderr,'export ALPINO_HOME=/home/your_user/your_tools/Alpino'
        sys.exit(-1)
    os.environ['SP_CSETLEN']='212'
    os.environ['SP_CTYPE']='utf8'

def load_sentences(in_obj):
    previous_sent = None
    previous_para = None
    current_sent = []
    sentences = []
    for token_obj in in_obj.get_tokens():
        token = token_obj.get_text()
        sent = token_obj.get_sent()
        para = token_obj.get_para()
        token_id = token_obj.get_id()
        if ((previous_sent is not None and sent != previous_sent) or
            (previous_para is not None and para != previous_para)):
            sentences.append(current_sent)
            current_sent = [(token,token_id)]
        else:
            current_sent.append((token,token_id))
        previous_sent = sent
        previous_para = para

    if len(current_sent) !=0:
        sentences.append(current_sent)
    return sentences

def get_term_type(pos):
    if pos in ['det','pron','prep','vg','conj' ]:
        return 'close'
    else:
        return 'open'

def node_to_penn(node,map_token_begin_node):
    children = node.getchildren()
    if len(children) == 0:
        word = node.get('word',None)
        if word is not None:
            #The attribute begin gives you the number of the token
            word = word.replace('(','-LRB')
            word = word.replace(')','-RRB-')

            num_token = node.get('begin')
            map_token_begin_node[num_token] = node
            word = num_token+'#'+word
            if node.get('rel') == 'hd':
                head = '=H'
            else:
                head = ''
            return '('+node.get('pos')+head+' '+word.encode('utf-8')+')'
        else:
            return ''
    else:
        str = '('+node.get('cat')+' '
        for n in children:
            str+=node_to_penn(n,map_token_begin_node)
        str+=')'
        return str

def xml_to_penn(filename):
    '''
    Converts the xml from Alpino into penntreebank format
    '''
    ## Under certain condition, there is know bug of Alpino, it sets the encoding in the XML
    ## to iso-8859-1, but the real encoding is UTF-8. So we need to force to use this encoding

    parser = etree.XMLParser(encoding='UTF-8')
    tree = etree.parse(filename,parser)
    ##This is a mapping for the token begin (0,1,2,...) to the <node element
    map_token_begin_node = {}

    str = node_to_penn(tree.find('node'),map_token_begin_node)
    return str,map_token_begin_node


def process_alpino_xml(xml_file,sentence,count_terms,knaf_obj,cnt_t,cnt_nt,cnt_edge):
    #sentence is a list of pairs [
    print>>sys.stderr,'Processing file',xml_file

    penn_tree_str, map_token_begin_node = xml_to_penn(xml_file)

    ##########################################
    #Create the term layer
    ##########################################

    term_ids = []
    lemma_for_termid = {}
    print>>sys.stderr,'  Creating the term layer...'
    for num_token, (token,token_id) in enumerate(sentence):
        new_term_id = 't_'+str(count_terms)
        count_terms+=1
        term_ids.append(new_term_id)
        alpino_node = map_token_begin_node[str(num_token)]
        term_obj = Cterm(type=knaf_obj.get_type())
        term_obj.set_id(new_term_id)
        new_span = Cspan()
        new_span.create_from_ids([token_id])
        term_obj.set_span(new_span)
        term_obj.set_lemma(alpino_node.get('lemma','unknown'))
        lemma_for_termid[new_term_id] = alpino_node.get('lemma','unknown')

        alppos = alpino_node.get('pos','unknown')
        term_obj.set_pos(alppos)
        term_obj.set_morphofeat(alpino_node.get('postag','unknown'))
        termtype = get_term_type(alppos)
        term_obj.set_type(termtype)
        knaf_obj.add_term(term_obj)

    ##########################################

    ##########################################
    ##Constituency layer
    print>>sys.stderr,'  Creating the constituency layer...'
    tree_obj,cnt_t,cnt_nt,cnt_edge = convert_penn_to_knaf_with_numtokens(penn_tree_str,term_ids,lemma_for_termid,cnt_t,cnt_nt,cnt_edge)
    knaf_obj.add_constituency_tree(tree_obj)
    ##########################################


    ##########################################
    # Dependency part
    ##########################################

    # Call to Alpino with the --treebank option to get the dependencies out of the XML
    print>>sys.stderr,'  Creating the dependency layer...'
    alpino_bin = os.path.join(os.environ['ALPINO_HOME'],'bin','Alpino')
    cmd = [alpino_bin, '-treebank_triples', xml_file]
    output = check_output(cmd)
    for line in output.splitlines():
        line = line.strip().decode('utf-8')
        my_dep = Calpino_dependency(line)
        if my_dep.is_ok():
            deps = my_dep.generate_dependencies(term_ids)
            for d in deps:
                knaf_obj.add_dependency(d)

    ##########################################

    # we return the counters for terms and consituent elements to keep generating following identifiers for next sentnces
    return count_terms,cnt_t,cnt_nt,cnt_edge

def run_morph_syn_parser(input_file, output_file, max_min_per_sent=None):

    set_up_alpino()

    in_obj = KafNafParser(input_file)

    lang = in_obj.get_language()
    if lang != 'nl':
        print>>sys.stdout,'ERROR! Language is ',lang,' and must be nl (Dutch)'
        sys.exit(-1)

    ## Sentences is a list of lists containing pairs token, tokenid
    #  [[(This,id1),(is,id2)...],[('The',id10)...
    sentences = load_sentences(in_obj)
    ####################

    # Create temporary folder to store the XML of Alpino
    out_folder_alp = tempfile.mkdtemp()
    ####################

    # Call to Alpinoo and generate the XML files
    alpino_bin = os.path.join(os.environ['ALPINO_HOME'],'bin','Alpino')
    cmd = alpino_bin
    if max_min_per_sent is not None:
        #max_min_per_sent is minutes
        cmd = cmd+' user_max=%d' % int(max_min_per_sent * 60 * 1000)  #converted to milliseconds
    cmd = cmd+' end_hook=xml -flag treebank '+out_folder_alp+' -parse'
    print>>sys.stderr,'Calling to Alpino at',os.environ['ALPINO_HOME'],'with',len(sentences),'sentences...'
    ##print>>sys.stderr,'CMD:%s' % cmd
    alpino_pro = Popen(cmd, stdin=PIPE, shell=True)
    for num_sentence, sentence in enumerate(sentences,1):
        alpino_pro.stdin.write('%d|' % num_sentence)
        for token,token_id in sentence:
            token = token.replace('[','\[')
            token = token.replace(']','\]')
            alpino_pro.stdin.write(token.encode('utf-8')+' ')
        alpino_pro.stdin.write('\n')
    alpino_pro.stdin.close()
    if alpino_pro.wait() != 0:
        raise Exception("Call to alpino failed (see logs): %s" % cmd)
    ####################
    # Process the XML files
    count_terms = 0
    cnt_t = cnt_nt = cnt_edge = 0
    for num_sent in range(len(sentences)):
        xml_file = os.path.join(out_folder_alp,str(num_sent+1)+'.xml')
        if os.path.exists(xml_file):
            count_terms,cnt_t,cnt_nt,cnt_edge = process_alpino_xml(xml_file,sentences[num_sent],count_terms,in_obj,cnt_t,cnt_nt,cnt_edge)
        else:
            print>>sys.stderr,'Not found the file',xml_file
    ####################

    ##Add the linguistic processors
    my_lp = Clp()
    my_lp.set_name(this_name)
    my_lp.set_version(version+'_'+last_modified)
    my_lp.set_timestamp()
    in_obj.add_linguistic_processor('terms',my_lp)

    my_lp_const = Clp()
    my_lp_const.set_name(this_name)
    my_lp_const.set_version(version+'_'+last_modified)
    my_lp_const.set_timestamp()
    in_obj.add_linguistic_processor('constituents',my_lp_const)

    my_lp_deps = Clp()
    my_lp_deps.set_name(this_name)
    my_lp_deps.set_version(version+'_'+last_modified)
    my_lp_deps.set_timestamp()
    in_obj.add_linguistic_processor('deps',my_lp_deps)
    ####################


    shutil.rmtree(out_folder_alp)
    in_obj.dump(sys.stdout)



if __name__ == '__main__':
    input_file = sys.stdin
    output_file = sys.stdout
    user_max = None

    parser = argparse.ArgumentParser(description='Morphosyntactic parser based on Alpino', version=version)
    parser.add_argument('-t', '--time', dest='max_minutes', type=float, help='Maximum number of minutes per sentence. Sentences that take longer will be skipped and not parsed (value must be a float)')

    args = parser.parse_args()

    run_morph_syn_parser(input_file,output_file, max_min_per_sent=args.max_minutes)

