
import json
import math
import os
import random
from collections import defaultdict

from rprojc import StandardProject


class Application(StandardProject):
    def __init__(self):
        super().__init__('UAT distances', proj_home=os.path.abspath('.'))
        self.data = self.ingest_uat(self.config['UAT_SOURCE_DATA'])
        self.str2uri = self.build_name_mapping()
    
    def persist(self):
        """Dump tree/mapping into the files"""

        with open(self.config['WORKDIR'] + '/uat.tree.json', 'w') as fo:
            fo.write(json.dumps(self.data))
        with open(self.config['WORKDIR'] + '/uat.synonyms.json', 'w') as fo:
            fo.write(json.dumps(self.str2uri))

    def ingest_uat(self, uat_file):
        """Extract useful data from UAT thesaurus"""
        with open(uat_file, 'r') as fi:
            j = json.load(fi)
        
        visited = defaultdict(dict)
        def harvest(node, level, parent):
            uri = node.get('uri')
            if uri is None:
                self.logger.error('Garbage inside UAT: node={}, level={}, parent={}'.format(node, level, parent))
                return
            uri = uri.rsplit('/', maxsplit=1)[-1]
            children = set()
            visited[uri] = {'uri': uri, 'name': node['name'], 'alt': node.get('altLabels', []) or [], 'children': children, 'level': level, 'id': len(visited), 'parent': parent}
            for child in node.get('children', []):
                childuri = child['uri'].rsplit('/', maxsplit=1)[-1]
                if childuri not in visited:
                    for id in harvest(child, level+1, uri):
                        if id:
                            children.add(id)
            return uri
                        
        # now go through the UAT structure and extract stuff we care about
        # UAT doesn't have one root, but there are ~10 top categories
        # by adding this extra dummy root, we are also penalizing terms
        # that apper is separate branches (which seems fair to me)
        root = {'uri': 'foo/root', 'children': j['children'], 'name': 'root', 'alt': []}
        harvest(root, 0, None)

        # turn children into list (to be easily serializable)
        for k,v in visited.items():
            v['children'] = list(v['children'])
        return visited
    
    def build_name_mapping(self):
        """Make it possible to map altLabels to nodes"""
        str2uri = {}

        for uri, attrs in self.data.items():
            str2uri[attrs['name']] = uri
            for alt in attrs['alt']:
                if alt in str2uri:
                    self.logger.warning('Possible problem with UAT data, altLabel is referenced by two different concepts: alt={} other={} this={}'.format(alt, str2uri[alt], uri))
                else:
                    str2uri[alt] = uri
        return str2uri


    def find_distance(self, v, w):
        """Find distance between two UAT terms (based on the structue of the UAT
        tree). We can resolve alt labels as well as canonical labels"""

        vuri = self.str2uri.get(v, None)
        wuri = self.str2uri.get(w, None)

        if vuri is None or wuri is None:
            raise Exception('A label is not present in UAT: v={}, w={}'.format(v, w))

        vlevel, wlevel = self.data[vuri]['level'], self.data[wuri]['level']

        # two options exist, either we are looking inside the same branch
        # or we are in two opposing branches of the tree. Either way, we
        # should find the closest common parent

        if vlevel > wlevel:
            vlevel, wlevel = wlevel, vlevel
            v,w = w,v
            vuri,wuri = wuri,vuri

        distance = 0
        
        # we have to walk this many steps to be on the same level
        xdiff = wlevel - vlevel
        xvuri,xwuri = vuri, wuri

        while xdiff and xwuri != 'root':
            distance += 1.0 / (self.data[xwuri]['level']+1)
            xwuri = self.data[xwuri]['parent'] # move one level higher
            xdiff -= 1

        
        # walk until we find the common ancestor
        while xvuri != xwuri:
            distance += 2 * (1.0 / (self.data[xwuri]['level']+1))
            xvuri, xwuri = self.data[xvuri]['parent'], self.data[xwuri]['parent']
        
        return (distance, self.data[xvuri]) # closest common ancestor



def test():
    a = Application()

    # so that we can load it elsewhere
    a.persist()

    # pick random pairs
    labels = list(a.str2uri.keys())
    random.shuffle(labels)
    i = 100

    while i:
        v, w = random.randint(0, len(labels)), random.randint(0, len(labels))
        if v == w:
            continue
        i -= 1
        
        d,ancestor = a.find_distance(labels[v], labels[w])
        print('{} \n Distance between v="{} (level={})" w="{} (level={})"\n closest ancestor={}'.format(
            d, labels[v], a.data[a.str2uri[labels[v]]]['level'], labels[w], a.data[a.str2uri[labels[w]]]['level'], ancestor))
    


if __name__ == '__main__':
    test()    
            

