import os
from rprojc import StandardProject
from cspatterns.datastructures import graphs

class Application(StandardProject):
    def __init__(self):
        super().__init__('UAT labels', proj_home=os.path.abspath('.'))
        self._id2str = []
        self._str2id = {}

    def id2label(self, id:int) -> str:
        return self._id2str.get(id, None)

    def label2id(self, label:str) -> int:
        if label not in self._str2id:
            self._str2id[label] = len(self._id2str)
            self._id2str.append(label)
        return self._str2id[label]


    def relax_edge(self, old_weight):
        return old_weight / 2.0


    def load_labels(self, datafile):
        
        if not os.path.exists(datafile):
            raise Exception('{} is not available'.format(datafile))

        graph = graphs.WeightedUndirectedGraph()
        for line in open(datafile, 'r'):
            parts = line.split('\t')
            bibcode, labels = parts[0], parts[1:]

            for i in range(len(labels)+1):
                j = i+1
                while j < len(labels):
                    v, w = self.label2id(labels[i]), self.label2id(labels[j])
                    weight = graph.get_weight(v, w, default=self.config.get('DEFAULT_EDGE_WEIGHT'))
                    graph.add(v, w, self.relax_edge(weight))
                    j += 1
        
        return graph


    def find_connected_components(self, graph):
        cc = 0
        visited = {}

        def dfs(v, seen, cc):
            seen[v] = cc
            for w, _ in graph.adj(v):
                if w not in seen:
                    dfs(w, seen, cc)

        for v in graph.vertices():
            if v not in visited:
                dfs(v, visited, cc)
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
        


def test():
    a = Application()
    print(a.config)
    g = a.load_labels(datafile = a.config.get('UAT_DATA', 'workdir/uat.test'))
    print('Loaded UAT graph, vertices: {}, edges: {}'.format(g.num_vertices(), g.num_edges()))

    print('Going to identify separate clusters (if any)')

    ccs = a.find_connected_components(g)
    print('Found {} connected components'.format(len(ccs)))

    for ic, cc in enumerate(ccs):
        print('{} vertices: {}, edges: {}'.format(ic, cc.num_vertices(), cc.num_edges()))

    