#!/usr/bin/env python

import logging
import os
import shutil
import sys
import tempfile
from io import BytesIO
from subprocess import Popen,PIPE, check_output

import requests
from KafNafParserPy import *
from lxml import etree
from lxml.etree import XMLSyntaxError

from .alpino_dependency import Calpino_dependency
from .convert_penn_to_kaf import convert_penn_to_knaf_with_numtokens

__version__ = "0.3"
this_name = 'Morphosyntactic parser based on Alpino'
last_modified = '2017-03-18'

###############################################

def set_up_alpino():
    ##Uncomment next line and point it to your local path to Alpino if you dont want to set the environment variable ALPINO_HOME
    #os.environ['ALPINO_HOME'] = '/home/izquierdo/tools/Alpino'
    if 'ALPINO_HOME' in os.environ:
        os.environ['SP_CSETLEN'] = '212'
        os.environ['SP_CTYPE'] = 'utf8'
        return 'local', os.environ['ALPINO_HOME']
    elif 'ALPINO_SERVER' in os.environ:
        return 'server', os.environ['ALPINO_SERVER']
    else:
        raise Exception('ALPINO_HOME or ALPINO_SERVER variables not set.'
                        'Set ALPINO_HOME to point to your local path to Alpino. For instance:\n'
                        'export ALPINO_HOME=/home/your_user/your_tools/Alpino')

def tokenize_local(paras, alpino_home):
    cmd = os.path.join(alpino_home, 'Tokenization', 'tok')
    sentnr = 1
    for parnr, para in enumerate(paras, start=1):
        p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE)
        out, _err = p.communicate(para.encode("utf-8"))
        for s in out.decode('utf-8').split("\n"):
            if s.strip():
                yield parnr, sentnr, s.strip()
                sentnr += 1

def add_tokenized_to_naf(naf, sentences):
    """Add the tokenized sentences to naf, returning and [(token, id), ..] list"""
    offset = 0
    old_parnr = None
    for parnr, sentnr, sentence in sentences:
        if old_parnr is not None and parnr != old_parnr:
            offset += 1 # character for line break
        sent = []
        for word in sentence.split():
            length = len(word)
            token = naf.create_wf(word, sentnr, offset=offset, length=length)
            offset += len(word) + 1
            token.set_para(str(parnr))
            sent.append((word, token.get_id()))
        yield sent

def tokenize(naf):
    """Tokenize the text in the NAF object and return [(token, id), ..] pairs

    Assumes that single line breaks are not relevant, and double lines breaks mark paragraphs
    """
    paras = [para.replace("\n", " ") for  para in re.split(r"\n\s*\n", naf.get_raw())]
    alpino_type, alpino_location = set_up_alpino()
    if alpino_type == "local":
        sentences = list(tokenize_local(paras, alpino_location))
    else:
        raise NotImplementedError("Tokenization via alpino-server is not implemented yet")
    return list(add_tokenized_to_naf(naf, sentences))

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
            return '('+node.get('pos')+head+' '+word+')'
        else:
            return ''
    else:
        str = '('+node.get('cat')+' '
        for n in children:
            str+=node_to_penn(n,map_token_begin_node)
        str+=')'
        return str

def xml_to_penn(tree):
    '''
    Converts the xml from Alpino into penntreebank format
    '''
    ##This is a mapping for the token begin (0,1,2,...) to the <node element
    map_token_begin_node = {}
    str = node_to_penn(tree.find('node'),map_token_begin_node)
    return str, map_token_begin_node


def process_alpino_xml(xml_tree, dependencies, sentence,count_terms,knaf_obj,cnt_t,cnt_nt,cnt_edge):
    penn_tree_str, map_token_begin_node = xml_to_penn(xml_tree)

    ##########################################
    #Create the term layer
    ##########################################

    term_ids = []
    lemma_for_termid = {}
    logging.info('Creating the term layer...')
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
    logging.info('Creating the constituency layer...')
    tree_obj,cnt_t,cnt_nt,cnt_edge = convert_penn_to_knaf_with_numtokens(penn_tree_str,term_ids,lemma_for_termid,cnt_t,cnt_nt,cnt_edge)
    knaf_obj.add_constituency_tree(tree_obj)
    ##########################################


    ##########################################
    # Dependency part
    ##########################################

    for my_dep in dependencies:
        if my_dep.is_ok():
            deps = my_dep.generate_dependencies(term_ids)
            for d in deps:
                knaf_obj.add_dependency(d)

    ##########################################

    # we return the counters for terms and consituent elements to keep generating following identifiers for next sentnces
    return count_terms,cnt_t,cnt_nt,cnt_edge


def call_alpino(sentences, max_min_per_sent):
    """Call alpino and yield (sentence, xml_tree, dependencies) tuples"""

    alpino_type, alpino_location = set_up_alpino()
    if alpino_type == 'local':
        return call_alpino_local(sentences, max_min_per_sent, alpino_location)
    else:
        return call_alpino_server(sentences, alpino_location)


def call_alpino_server(sentences, server):
    ## Under certain condition, there is know bug of Alpino, it sets the encoding in the XML
    ## to iso-8859-1, but the real encoding is UTF-8. So we need to force to use this encoding
    parser = etree.XMLParser(encoding='UTF-8')
    url = "{server}/parse".format(**locals())
    text = "\n".join(sentences_from_naf(sentences))
    r = requests.post(url, json=dict(output="treebank_triples", text=text))
    r.raise_for_status()
    for sid, results in r.json().items():
        sentence = sentences[int(sid)-1]
        tree = etree.fromstring(results['xml'].encode("utf-8"), parser)
        dependencies = [Calpino_dependency(dep) for dep in results['triples']]
        yield sentence, tree, dependencies


def sentences_from_naf(sentences):
    for i, sentence in enumerate(sentences, 1):
        sent = " ".join(token.replace('[', '\[').replace(']', '\]') for token, _token_id in sentence)
        yield u"{i}|{sent}".format(**locals())

def call_alpino_local(sentences, max_min_per_sent, alpino_home):
    ## Under certain condition, there is know bug of Alpino, it sets the encoding in the XML
    ## to iso-8859-1, but the real encoding is UTF-8. So we need to force to use this encoding
    parser = etree.XMLParser(encoding='UTF-8')

    # Create temporary folder to store the XML of Alpino
    out_folder_alp = tempfile.mkdtemp()
    ####################

    # Call to Alpinoo and generate the XML files
    cmd = os.path.join(alpino_home, 'bin', 'Alpino')
    if max_min_per_sent is not None:
        # max_min_per_sent is minutes
        cmd += ' user_max=%d' % int(max_min_per_sent * 60 * 1000)  # converted to milliseconds
    cmd += ' end_hook=xml -flag treebank ' + out_folder_alp + ' -parse'
    logging.info('Calling Alpino with {} sentences'.format(len(sentences)))
    logging.debug("CMD: {}".format(cmd))
    alpino_pro = Popen(cmd, stdin=PIPE, shell=True)
    for sentence in sentences_from_naf(sentences):
        alpino_pro.stdin.write(sentence.encode("utf-8"))
        alpino_pro.stdin.write(b'\n')
    alpino_pro.stdin.close()
    if alpino_pro.wait() != 0:
        raise Exception("Call to alpino failed (see logs): %s" % cmd)

    # Parse results, get dependencies, and yield sentence results
    for i, sent in enumerate(sentences):
        xml_file = os.path.join(out_folder_alp, str(i+1)+'.xml')
        if not os.path.exists(xml_file):
            logging.warning('Not found the file {}'.format(xml_file))
            continue

        tree = etree.parse(xml_file, parser)

        # Create dependency layer by calling alpino again with -treebank_triples
        logging.info('Creating the dependency layer...')
        alpino_bin = os.path.join(alpino_home, 'bin', 'Alpino')
        cmd = [alpino_bin, '-treebank_triples', xml_file]
        output = check_output(cmd)
        dependencies = [Calpino_dependency(line.strip().decode('utf-8')) for line in output.splitlines()]
        # Yield sentence, parsed XML tree, and dependencies
        yield sent, tree, dependencies

    # Cleanup
    shutil.rmtree(out_folder_alp)

def get_naf(input_file):
    # We need to buffer the input since otherwise it will be lost if the parser fails
    input = input_file.read()
    try:
        naf = KafNafParser(BytesIO(input))
    except XMLSyntaxError:
        input = input.decode("utf-8")
        if "<NAF" in input and "</NAF>" in input:
            # I'm guessing this should be a NAF file but something is wrong - let's raise it
            logging.exception("Error parsing NAF file")
            raise
        naf = KafNafParser(type="NAF")
        naf.set_version("3.0")
        naf.set_language("nl")
        naf.lang = "nl"
        naf.raw = input
        naf.set_raw(naf.raw)
    return naf


def parse(input_file, max_min_per_sent=None):
    if isinstance(input_file, KafNafParser):
        in_obj = input_file
    else:
        in_obj = get_naf(input_file)

    lang = in_obj.get_language()
    if lang != 'nl':
        logging.warning('ERROR! Language is {} and must be nl (Dutch)'.format(lang))
        sys.exit(-1)

    ## Sentences is a list of lists containing pairs token, tokenid
    #  [[(This,id1),(is,id2)...],[('The',id10)...
    if in_obj.text_layer is None:
        sentences = tokenize(in_obj)
    else:
        sentences = load_sentences(in_obj)
    ####################

    ####################
    # Process the XML files
    count_terms = 0
    cnt_t = cnt_nt = cnt_edge = 0
    for sentence, tree, dependencies in call_alpino(sentences, max_min_per_sent):
        count_terms,cnt_t,cnt_nt,cnt_edge = process_alpino_xml(tree, dependencies, sentence,count_terms,in_obj,cnt_t,cnt_nt,cnt_edge)
    ####################



    ##Add the linguistic processors
    my_lp = Clp()
    my_lp.set_name(this_name)
    my_lp.set_version(__version__+'_'+last_modified)
    my_lp.set_timestamp()
    in_obj.add_linguistic_processor('terms',my_lp)

    my_lp_const = Clp()
    my_lp_const.set_name(this_name)
    my_lp_const.set_version(__version__+'_'+last_modified)
    my_lp_const.set_timestamp()
    in_obj.add_linguistic_processor('constituents',my_lp_const)

    my_lp_deps = Clp()
    my_lp_deps.set_name(this_name)
    my_lp_deps.set_version(__version__+'_'+last_modified)
    my_lp_deps.set_timestamp()
    in_obj.add_linguistic_processor('deps',my_lp_deps)
    ####################

    return in_obj
