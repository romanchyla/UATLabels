# Exploration of the UAT hiearchy and keywords


## Installation

```
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r dev-requirements.txt
```


## Usage

```bash
python app.py

```


Example output:

```bash

Loaded UAT graph, V=1574, E=38724
- pruned the graph, V=1191, E=13932
Going to identify separate graphs (if any) - after we have deleted edges not used more than 1 times
Found 2 connected components
CC: 0 V=1189, E=13931
-- written into: /dvt/workspace/UATLabels/workdir/graph.0
--- Attempting to split connected component into 10 minimal spanning trees
---- /dvt/workspace/UATLabels/workdir/graph.0.0, V=1180, E=1179
CC: 1 V=2, E=1
-- written into: /dvt/workspace/UATLabels/workdir/graph.1
--- Attempting to split connected component into 10 minimal spanning trees
---- /dvt/workspace/UATLabels/workdir/graph.1.0, V=2, E=1
Going to calculate distances between a paper and selected concepts
4 labels were missing: {'Dirac cosmology', 'Spectrophotometric standards', 'Astronomy education', 'Astronomical location'}
```


Results are saved into `workdir`

For example, the following file will list distances for every paper (`workdir/uat.csv`). The distances are simple means; if you need anything fancier modify the `app.py`

```
head workdir/uat.csv.distances 
bibcode	Astrophysical processes	Cosmology	Exoplanet astronomy	Galactic and extragalactic astronomy	High energy astrophysics	Interdisciplinary astronomy	Interstellar medium	Observational astronomy	Solar physics	Solar system astronomy	Stellar astronomy
2019AJ....158....1K	1.7319929604679913	1.100296166775328	2.6543279274580054	0.9740248554241532	2.634360532869616	1.5206197990329824	0.47226265829572	0.7378475181478632	1.8950034625785641	2.8369554919502766	3.4879488273761092
2019AJ....158..117C	3.111072744820074	2.609009042424344	2.407751188235539	2.482737731073169	3.1674189595218167	2.2460375644703787	1.851342442647803	2.4040119519810723	3.274083246930647	3.370013918602478	3.2413720881536427
2019AJ....158..119L	6.6433845325655305	6.442314713094556	5.423422080421928	6.316043401743381	4.291018505051956	5.45151834275849	5.383654230393259	6.079866064467092	6.806395034676103	6.190776019320199	5.980268202572616
2019AJ....158..122K	5.131585775289146	4.780019014355794	4.852124541065411	4.653747703004619	3.3235682085325045	4.103135090210779	3.8718554731168755	4.496296144820426	5.2945962773997195	5.034752105557683	5.685745440983514
2019AJ....158..137S	2.069435809749049	1.3209949047835088	3.121635927825199	1.194723593432334	3.1016685332368095	1.9879277994001756	0.9395706586629134	1.3128122620704787	2.3623114629457573	3.3042634923174705	3.9552568277433027
2019AJ....158..149L	1.6324842007219835	1.6045679160325232	2.208782354250973	1.4782966046813486	2.1888149596625834	1.267433564611145	0.545907433331226	1.2421192674050585	1.96864823761407	2.391409918743244	3.0424032541690766
2019AJ....158..150B	3.598004015262448	3.396934195791474	2.962767937524846	3.270662884440299	2.9428005429364568	2.4061378254554087	2.3382737130901767	3.034485547164009	3.7610145173730207	2.117598817277616	3.7963888374429495
2019AJ....158..156G	6.206182691042076	6.005112871571102	5.570946613304475	5.878841560219927	3.288095811799308	5.014316501235037	4.946452388869805	5.642664222943638	6.369193193152649	5.753574177796746	6.4045675132225774
2019AJ....158..159B	3.8206600251268252	3.619590205655851	3.185423947389223	3.493318894304676	3.1654565528008343	2.628793835319786	2.5609297229545542	3.257141557028387	3.983670527237398	1.312458142402492	4.019044847307327

```



## Explanation


First, we build an undirected graph out of all keywords - as asigned to each individual paper. If a paper had `labelA, labelB, labelC` - then we'll generate 3 pairs: `labelA-labelB`, `labelA-labelC`, `labelB-labelC`

In the example above, we have a graph with 1574 vertices and 38724 edges (pairs).

Next, we prune the edges -- removing anything which occurs less than `EDGE_PRUNE_MIN` times. In our case, removing any pair that just occurs once -- it cuts down the number of connections to 13932.

Right now, the edge weights are simply frequencies -- we'll transform them to be `1/log(freq)` (if you want to play with other types of weight, modify method `transform_weights` https://github.com/romanchyla/UATLabels/blob/master/app.py#L97) -- this way the most frequent edges will be given the smallest weight.

Following the weights, we are going to discover **minimum spanning tree** -- i.e. tree made of all vertices, minimizing the path from one vertex to another; the idea is to have labels that frequenty occur together to be closest to each other.

Note: you can play with `NUM_SUBGRAPHS` to generate different MST (i.e. less complete trees; it seems like when we stop the graph earlier, we get more stronger connections -- at the expense of excluding less frequent ones; to see examples checkout `workdir/graph.0.x` files).

So now we have a MST (map of distances between labels), in the last phase, we'll calculate distances **from selected labels** to every label assigned to a paper. For example, UAT contains 11 concepts in the top hierarchy:

    ```
    Astrophysical processes
    Cosmology
    Exoplanet astronomy
    Galactic and extragalactic astronomy
    High energy astrophysics
    Interdisciplinary astronomy
    Interstellar medium
    Observational astronomy
    Solar physics
    Solar system astronomy
    Stellar astronomy
    ```

For each of these concepts, we build another datastructure which allows us to efficiently discover distances from labels to top label.

Then we go through every paper once again and calculate how far/close its keywords are to each `top label`. The result a simple arithmetic mean (again: anything fancier, please modify the code). If there exists no path (even if just for one label), the distance becomes infinite.


## Playtime

You can modify `config.py` and/or the code -- the algorithms are efficient enough to be able to process huge graphs (millions or edges) and `O(ElogV)` time.


## Distance between labels from the UAT thesaurus

You can import `dist.py` and then use that program to print distances between two labels (as extracted from the UAT graph).

It works the following way:

1. First we import UAT (config `UAT_SOURCE_DATA`) and extract parent, children, and alternate labels
1. Then we map all the names to uri (so that you can use synonyms to retrieve nodes)
1. Lastly, we calculate distance between two labels (see: `Application:find_distances()`)

Basically, we'll walk upwards from the deepest node -- now both nodes (labels) are on the same level; we continue walking upwards until we discover **common ancestor** all the while keeping track of number of steps we took. The method will return the distance and also the data about the ancestor.

Here is an output for some randomly selected pairs:


```
Distance between v="Goedel universe" w="Lunar mineralogy" d=8, closest ancestor={'uri': 'root', 'name': 'root', 'alt': [], 'children': {'3', '5', '1', '6', '7', '9', '8', '2', '0', '4'}, 'level': 0, 'id': 0, 'parent': None}
Distance between v="Barium stars" w="Modified gravity" d=9, closest ancestor={'uri': 'root', 'name': 'root', 'alt': [], 'children': {'3', '5', '1', '6', '7', '9', '8', '2', '0', '4'}, 'level': 0, 'id': 0, 'parent': None}
Distance between v="PSB" w="High energy astronomy" d=4, closest ancestor={'uri': 'root', 'name': 'root', 'alt': [], 'children': {'3', '5', '1', '6', '7', '9', '8', '2', '0', '4'}, 'level': 0, 'id': 0, 'parent': None}
Distance between v="FRBs" w="Unbarred spiral galaxies" d=9, closest ancestor={'uri': 'root', 'name': 'root', 'alt': [], 'children': {'3', '5', '1', '6', '7', '9', '8', '2', '0', '4'}, 'level': 0, 'id': 0, 'parent': None}
Distance between v="Zero-age horizontal branch stars" w="ZHR" d=11, closest ancestor={'uri': 'root', 'name': 'root', 'alt': [], 'children': {'3', '5', '1', '6', '7', '9', '8', '2', '0', '4'}, 'level': 0, 'id': 0, 'parent': None}
Distance between v="Milky Way Galaxy fountains" w="White dwarf stars" d=8, closest ancestor={'uri': 'root', 'name': 'root', 'alt': [], 'children': {'3', '5', '1', '6', '7', '9', '8', '2', '0', '4'}, 'level': 0, 'id': 0, 'parent': None}
Distance between v="Lightcurves" w="Extragalactic Distance Scale" d=4, closest ancestor={'uri': '1684', 'name': 'Astronomical techniques', 'alt': ['Observation techniques', 'Techniques'], 'children': {'3', '5', '1', '6', '7', '9', '8', '2', '0', '4'}, 'level': 2, 'id': 1133, 'parent': '1145'}
Distance between v="NEP" w="Photospheres" d=11, closest ancestor={'uri': 'root', 'name': 'root', 'alt': [], 'children': {'3', '5', '1', '6', '7', '9', '8', '2', '0', '4'}, 'level': 0, 'id': 0, 'parent': None}
Distance between v="Near ultraviolet telescopes" w="Poor clusters" d=7, closest ancestor={'uri': 'root', 'name': 'root', 'alt': [], 'children': {'3', '5', '1', '6', '7', '9', '8', '2', '0', '4'}, 'level': 0, 'id': 0, 'parent': None}
```