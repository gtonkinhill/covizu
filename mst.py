import math
import networkx as nx
from networkx.algorithms import tree
import sys


print("populate complete graph with TN93 distances")
G = nx.Graph()
with open('data/clusters.tn93.csv') as f:
    _ = next(f)
    for line in f:
        id1, id2, dist = line.strip().split(',')
        for node in [id1, id2]:
            if node not in G:
                G.add_node(node)
        G.add_edge(id1, id2, weight=float(dist))


# generate minimum spanning tree
print("generating minimum spanning tree")
mst = tree.minimum_spanning_tree(G, weight='weight')


def get_edgelist(g):
    edgelist = {}
    for n1, n2, dist in g.edges(data='weight'):
        if n1 not in edgelist:
            edgelist.update({n1: {}})
        edgelist[n1].update({n2: dist})
        if n2 not in edgelist:
            edgelist.update({n2: {}})
        edgelist[n2].update({n1: dist})
    return edgelist


# count the number of cases per cluster
print('counting number of cases per cluster')
clusters = {}
with open('data/clusters.info.csv') as f:
    _ = next(f)
    for line in f:
        label, _, _, _, _ = line.strip().split(',')
        acc = label.split('|')[1]
        if acc not in G:
            # omitted some clusters with missing dates
            continue
        if acc not in clusters:
            clusters.update({acc: 0})
        clusters[acc] += 1

# traverse MST from earliest label (cluster)
# search edge list for children of root node and recurse
def traversal(node, parent, edgelist, history):
    history.append(node)
    yield (node, parent)
    children = [child for child, _ in edgelist[node].items()
                if child not in history]
    for child in children:
        for obj in traversal(child, node, edgelist, history=history):
            yield obj


# root the MST on the cluster with most cases
intermed = [(count, node) for node, count in clusters.items()]
intermed.sort(reverse=True)
root = intermed[0][1]


# write clusters out to file
dotfile = open('mst/mst.dot', 'w')
dotfile.write('digraph {\nrankdir=LR;\n')
#dotfile.write('  node [label="" shape="circle"];\n')

for node, count in clusters.items():
    dotfile.write('  "{}" [width={}];\n'.format(
        node, math.sqrt(count)/10.
    ))

edgelist = get_edgelist(mst)
dg = nx.DiGraph()

for child, parent in traversal(root, None, edgelist, history=[]):
    if parent is None:
        continue

    # cut at nodes with outdegree of 20+
    if mst.degree[child] > 15:  #if clusters[child] > 10:
        continue

    #outfile.write("{},{},{}\n".format(parent, child, clusters[child]))
    dotfile.write('  "{}"->"{}" [len={}];\n'.format(
        parent, child, edgelist[parent][child] / 0.0001
    ))
    dg.add_edge(parent, child)

#outfile.close()
dotfile.write('}\n')
dotfile.close()

components = list(nx.weakly_connected_components(dg))

for i, comp in enumerate(components):
    outfile = open('mst/component-{}.edgelist.csv'.format(i), 'w')
    outfile.write('parent,child,dist\n')

    sg = nx.subgraph(dg, comp)
    for parent, child in sg.edges():
        dist = edgelist[parent][child]
        outfile.write('{},{},{}\n'.format(parent, child, dist))

    outfile.close()


# dot -Kneato -Tpdf mst/mst.dot > mst/mst.dot.pdf
