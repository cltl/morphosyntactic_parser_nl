from xml.sax.saxutils import escape

from KafNafParserPy import *
from lxml import etree

from .tree import Tree


## will be used as global variables to generate recursively the KAF constituent nodes
NOTER='nonter'
TER='ter'
EDGE='edge'
noter_cnt=0
ter_cnt=0
edge_cnt=0

##This function generates a "tree" xml element as defined in KAF from a string containing
##the penntreebank format and a list of term ids to do the linking
'''           
s = '(S (NP (DET The) (NN dog)) (VP (V ate) (NP (DET the) (NN cat))) (. .))'
ids = ['t0 t1','t2','t3','t4','t5','t6']
tree_node = create_constituency_layer(s, ids)
e = etree.ElementTree(element=tree_node)
e.write(sys.stdout,pretty_print=True)
'''

list_t = []
cnt_t = 0
list_nt = []
cnt_nt =0
list_edge = []
cnt_edge =0

def convert_penn_to_knaf_with_numtokens(tree_str,term_ids,lemma_for_termid,off_t=0,off_nt=0,off_edge=0):
    global list_t, list_nt,list_edge,cnt_t, cnt_nt, cnt_edge
    list_t = []
    list_nt = []
    list_edge = []
    cnt_t = off_t
    cnt_nt = off_nt
    cnt_edge = off_edge

    this_tree = Tree(tree_str)
    for num, num_token_and_token in enumerate(this_tree.leaves()):
        ## token is not used at all
        ##print num,token,position,token_id
        p = num_token_and_token.find('#')
        num_token = int(num_token_and_token[:p])
        position = this_tree.leaf_treeposition(num)
        token_id = term_ids[int(num_token)]
        this_tree[position] = token_id

    ##Creat the ROOT
    create_extra_root = False
    nt_id = None
    if create_extra_root:
        nt_id = 'nter'+str(cnt_nt)
        cnt_nt +=1
        list_nt.append((nt_id,'ROOT'))
    
    visit_node(this_tree, nt_id)
 
    this_tree = Ctree()
    nonter_heads = set()
    #Nonter
    labels_for_nt = {}
    for nt_id, label in list_nt:
        ##Checking the head
        if len(label)>=2 and label[-1]=='H' and label[-2]=='=':
            nonter_heads.add(nt_id)
            label = label[:-2]
        nt_obj = Cnonterminal()
        nt_obj.set_id(nt_id)
        nt_obj.set_label(label)
        labels_for_nt[nt_id] = label
        this_tree.append_element(nt_obj)
    
    ## Terminals
    lemma_for_ter = {}
    for ter_id, span_ids in list_t:
        ter_obj = Cterminal()
        ter_obj.set_id(ter_id)
        this_span = Cspan()
        term_ids = span_ids.split(' ')
        this_span.create_from_ids(term_ids)  
        ter_obj.set_span(this_span)      
        lemma_for_ter[ter_id] = lemma_for_termid[term_ids[-1]]
        this_tree.append_element(ter_obj)
        
    ##Edges
    #for edge_id,node_to,node_from in list_edge:
    for edge_id, node_from, node_to in list_edge:
        edge_obj = Cedge()
        edge_obj.set_id(edge_id)
        edge_obj.set_from(node_from)
        edge_obj.set_to(node_to)
        
        ## For the comment
        ##Only non-ter
        label_to = labels_for_nt.get(node_to)
        
        ##Could be ter or nonter
        label_from = labels_for_nt.get(node_from)
        if label_from is None:
            label_from = lemma_for_ter.get(node_from,'kk')
                                        
        comment = '  '+(edge_id)+'  '+(label_to)+' <- '+(label_from)+' '
        comment = escape(comment.replace('--','-'))
        if node_from in nonter_heads:
            edge_obj.set_as_head()
        edge_obj.set_comment(comment)
        this_tree.append_element(edge_obj)
    
    return this_tree,cnt_t,cnt_nt,cnt_edge
        


def visit_node(node,id_parent=None):
    global list_t, list_nt,list_edge,cnt_t, cnt_nt, cnt_edge

    if isinstance(node,str): #is a terminal
        ##Create the terminal
        t_id = 'ter'+str(cnt_t)
        cnt_t +=1
        list_t.append((t_id,str(node)))
        
        ##Create the edge with the parent
        edge_id = 'tre'+str(cnt_edge)
        cnt_edge +=1
        list_edge.append((edge_id,t_id,id_parent))
    else:  #Is a non terminal
        ##Create the nonterminal
        nt_id = 'nter'+str(cnt_nt)
        cnt_nt+=1
        list_nt.append((nt_id,node.node))
        
        ##Create the linking with the parent
        if id_parent is not None:
            edge_id = 'tre'+str(cnt_edge)
            cnt_edge +=1
            list_edge.append((edge_id,nt_id,id_parent))
        
        ##Call to the child
        for child in node:
            visit_node(child,nt_id)
            
        
    
if __name__ == '__main__':
    s = "(S (NP (DET 0#The) (NN 1#dog)) (VP (V 2#ate) (NP (DET 3#the) (NN 4#cat))) (. 5#.))"
    ids = ['t0' ,'t1','t2','t3','t4','t5']
    t= {}
    t['t0']='The'
    t['t1']='dog'
    t['t2']='ate'
    t['t3']='the'
    t['t4']='cat'
    t['t5']='.'
    root = convert_penn_to_kaf_with_numtokens(s,ids,None,t)
    import sys
    etree.ElementTree(element=root).write(sys.stdout,pretty_print=1)



    
    
