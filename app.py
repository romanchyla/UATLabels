import os
import heapq
import math
from rprojc import StandardProject
from cspatterns.datastructures import graphs, unionfind
from cspatterns.greedy import mst
from collections import defaultdict

class Application(StandardProject):
    def __init__(self):
        super().__init__('UAT labels', proj_home=os.path.abspath('.'))
        self._id2str = []
        self._str2id = {}

    def id2label(self, id:int) -> str:
        return self._id2str[id]

    def label2id(self, label:str) -> int:
        if label not in self._str2id:
            self._str2id[label] = len(self._id2str)
            self._id2str.append(label)
        return self._str2id[label]


    def weigh_edge(self, v, w, old_weight):
        return old_weight + 1


    def load_graph(self, datafile):
        """
        Loads UAT graph from csv file of the format
        bibcode\tlabel\tlabel
        """
        if not os.path.exists(datafile):
            raise Exception('{} is not available'.format(datafile))

        graph = graphs.WeightedUndirectedGraph()
        for line in open(datafile, 'r'):
            parts = list(filter(lambda x: x.strip(), line.strip().split('\t')))
            bibcode, labels = parts[0], parts[1:]

            for i in range(len(labels)+1):
                j = i+1
                while j < len(labels):
                    v, w = self.label2id(labels[i]), self.label2id(labels[j])
                    weight = graph.get_weight(v, w, default=self.config.get('DEFAULT_EDGE_WEIGHT'))
                    graph.add(v, w, self.weigh_edge(v, w, weight))
                    j += 1
        
        return graph

    def prune_edges(self, graph, min_weight):
        for v, w, weight in graph.edges():
            if weight < min_weight:
                graph.delete_edge(v, w)

    def transform_weights(self, graph):
        maxw = 0
        for v, w, weight in graph.edges():
            graph.add(v, w, 1.0 / max(1.0, (math.log(weight))))

    def find_connected_components(self, graph):
        cc = 0
        visited = {}

        for v in graph.vertices():
            if v not in visited:
                stack = [v]
                while stack:
                    v = stack.pop()
                    if v in visited:
                        continue
                    visited[v] = cc
                    for w, _ in graph.adj(v):
                        if w not in visited:
                            stack.append(w)
                cc += 1

        if cc == 1:
            return [graph]

        # build separate graphs out of the cc
        ccs = [set() for _ in range(cc)]
        grs = [graphs.WeightedUndirectedGraph() for _ in range(cc)]

        for v, c in visited.items():
            ccs[c].add(v)

        for ic, cc in enumerate(ccs):
            for v in cc:
                for w,weight in graph.adj(v):
                    grs[ic].add(v, w, weight)
        
        return grs

    def dump_graph(self, graph, location):
        with open(location, 'w') as fo:
            for v,w,weight in graph.edges():
                fo.write('{}\t{}\t{}\n'.format(self.id2label(v), self.id2label(w), weight))
        

    def split_graph(self, graph, stop_at=2):
        """
        Basically, we are going to use Kruskal alg to identify 
        minimum spanning trees (the most frequent edges have the
        smallest weights). We'll stop once we have reached 'stop_at'
        number of components"""

        union = unionfind.UnionFind()
        pq = []
        for v,w,weight in graph.edges():
            pq.append((weight, v, w))
            union.get_key(v)
            union.get_key(w)
        heapq.heapify(pq)

        
        
        while pq:
            weight, v, w = heapq.heappop(pq)
            if not union.is_connected(v, w):
                union.join(v, w)
                #print('union_size={}'.format(union.num_components()))
                #if union.num_components() <= stop_at:
                stop_at -= 1
                if not stop_at:
                    print('Stopping while len(pq)={}, union_size={}'.format(len(pq), union.num_components()))
                    break

        # now what remains is to read the union and 
        # reconstruct the spanning tree
        data = union.compress()
        mst = defaultdict(graphs.WeightedUndirectedGraph)
        seen = {}
        #print(set(data), len(data))
        for i, parent in enumerate(data):
            for w, weight in graph.adj(i):
                if data[w] != parent:
                    continue  # this edge is not part of the same MST
                mst[parent].add(i, w, weight)

        return mst.values()




def test():
    app = Application()
    
    graph = app.load_graph(datafile = app.config.get('UAT_DATA', 'workdir/uat.test'))
    print('Loaded UAT graph, vertices: {}, edges: {}'.format(graph.num_vertices(), graph.num_edges()))

    print('Going to identify separate graphs (if any) - after we have deleted edges not used more than {} times'.format(app.config.get('EDGE_PRUNE_MIN', -1)))
    app.prune_edges(graph, app.config.get('EDGE_PRUNE_MIN', -1))
    app.transform_weights(graph)

    connected_components = app.find_connected_components(graph)
    print('Found {} connected components'.format(len(connected_components)))

    workdir = app.config['WORKDIR']
    for ic, cc in enumerate(connected_components):
        loc = workdir + '/graph.{}'.format(ic)
        print('CC: {} V={}, E={}'.format(ic, cc.num_vertices(), cc.num_edges()))
        
        app.dump_graph(cc, loc)
        print('-- written into: {}'.format(loc))

        split = app.config.get('NUM_SUBGRAPHS')
        print('--- Attempting to split connected component into {} minimal spanning trees'.format(split))
        kruskal = mst.KruskalMST(cc)

        tree = written = None
        for size, tree in kruskal.iter():
            if size <= split:
                for iic, subcc in enumerate(tree.find_connected_components()):
                    subgraph = graphs.WeightedUndirectedGraph(*subcc)
                    app.dump_graph(subgraph, loc + '.{}'.format(iic))
                    print('---- found: {}, V={}, E={}'.format(iic, subgraph.num_vertices(), subgraph.num_edges()))
                written = True
                break
        if not written:
            app.dump_graph(tree, loc + '.{}'.format(tree))

        

if __name__ == '__main__':
    test()    