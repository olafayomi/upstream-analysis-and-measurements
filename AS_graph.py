#!/usr/bin/env python

import networkx as nx
import sys
import re
import time
import inspect
import csv
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import numpy
from networkx import path_graph, random_layout
import argparse


def readASRelData(ASRelDataFile):
    with open(ASRelDataFile, 'r') as f:
        try:
            ASRelData = csv.reader(f, delimiter='\t')
            graph = createGraph(ASRelData)
        except IndexError:
            ASRelData = csv.reader(f, delimiter='|')
            graph = createGraph(ASRelData)
        
    return graph
        #printASRelData(ASRelData)


def generateASGraph():
    random = numpy.random.seed(1000000)
    internetGraph = nx.random_internet_as_graph(30, seed=random)
    return internetGraph


def createGraph(ASRelData):
    internetGraph = nx.DiGraph()
    for asRelLink in ASRelData:
        if asRelLink[2] != 'unknown':
            if (asRelLink[2] == 'p2c') or (asRelLink[2] == '-1'):
                internetGraph.add_edge(asRelLink[0], asRelLink[1],
                                       relationship='p2c')

            if (asRelLink[2] == 'c2p'):
                internetGraph.add_edge(asRelLink[1], asRelLink[0],
                                       relationship='p2c')

            if (asRelLink[2] == 'p2p') or (asRelLink[2] == '0'):
                internetGraph.add_edge(asRelLink[0], asRelLink[1],
                                       relationship='p2p')
                internetGraph.add_edge(asRelLink[1], asRelLink[0],
                                       relationship='p2p')

    #return internetGraph
    return internetGraph.reverse()


def drawTopoGraph(graph):
    plt.subplot(111)
    pos = nx.spring_layout(graph)
    #nodes = nx.draw_networkx_nodes(graph, pos, with_labels=True)
    nodes = nx.draw_networkx_nodes(graph, pos)
    p2c_edges,  p2p_edges = seperateEdges(graph)
    edge_colors = ['r' if edge in p2c_edges else 'g' for edge in graph.edges]
    #print("edge_colors: %s\n" % edge_colors)
    nodes.set_edgecolor('r')
    nx.draw_networkx_edges(graph, pos)
    nx.draw_networkx_edges(graph, pos, edge_color=edge_colors, min_source_margin=3, min_target_margin=3 )
    #nx.draw_networkx_edges(graph, pos, edge_list=p2p_edges, edge_color='g')
    nodeList = list(graph.nodes)
    labels = {}
    for node in  nodeList:
        labels[node] = 'ASN'+node
    nx.draw_networkx_labels(graph, pos, labels, font_weight='bold')
    #nx.draw(graph, with_labels=True, font_weight='bold')
    plt.show()
    #plt.savefig("inetTopo.png")


def drawDegHistogram(degHistList, graph):
    num_bins = 5
    n, bins, patches = plt.hist(list(dict(nx.degree(graph)).values()), num_bins, facecolor='red', alpha=0.1)
    plt.show()


def getMaxNeighbour(adjGraph):
    max_length = 0
    for node, adj_list in adjGraph:
        if len(adj_list) >= max_length:
            maxNode = node
            max_length = len(adj_list)
            neighbours = adj_list
    return neighbours, maxNode

def getNeighbour(adjGraph, tnode):
    for node, adj_list in adjGraph:
        if tnode == node:
            return adj_list

def analyseGraph(graph):
    #print("Total number of edges in topology graph is: %s\n" % graph.number_of_edges())
    #print("Total number of nodes in topology graph is: %s\n" % graph.number_of_nodes())
    #print("Density of topology graph is: %s\n" % nx.density(graph))
    #print("Topology graph informantion: %s\n" % nx.info(graph))
    getMaxNeigh, getMaxNode = getMaxNeighbour(graph.adjacency())
    print("Node with the highest number of neighbours: %s\n" % getMaxNode)
    return(getMaxNeigh, getMaxNode)


def createSubgraph(graph, node, neighbourNodes):
    if type(neighbourNodes) is not list:
        allNodes = list(neighbourNodes)
    else:
        allNodes = neighbourNodes
    allNodes.append(node)
    subgraphMaxNode = nx.subgraph(graph, allNodes)
    return subgraphMaxNode


def printASRelData(ASRelData):
    for line in ASRelData:
        print("Line: %s\n" % line)

def seperateEdges(graph):
    p2c_edges = []
    p2p_edges = []
    for edge in list(graph.edges):
        rel = graph.get_edge_data(edge[0],edge[1])
        #print("Attribute rel is %s\n" %rel) 
        if rel['relationship'] == 'p2c':
            p2c_edges.append(edge)

        if rel['relationship'] == 'p2p':
            p2p_edges.append(edge)
    return p2c_edges, p2p_edges

if __name__ == "__main__":
    #if len(sys.argv) < 2:
    #    print("Usage: AS_graph.py datafile\n")
    #    sys.exit(-1)
    argParser = argparse.ArgumentParser(
            description='Get neighbors of an AS and subgraph',
            usage='%(prog)s [-I as-rel.datafile -A target ASN -O asn_relation_file]')
    argParser.add_argument('-I', dest='as_rel_data', help='AS relation data file',
                           default=None)
    argParser.add_argument('-A', dest='ASN', help='Target AS number',
                           default=None)
    argParser.add_argument('-O', dest='target_as_rel', help='Target AS relation file output',
                           default='filtered-as-rel.txt')
    args = argParser.parse_args()

    if (args.as_rel_data is None) or (args.ASN is None):
        print("AS relationship data file or target AS number not passed!!!\n")
        sys.exit(-1)

    graphData = readASRelData(args.as_rel_data)
    mNodeNeighbors, mNode = analyseGraph(graphData)
    maxNeigh, maxNode = getMaxNeighbour(graphData.adjacency())
    neighbours = getNeighbour(graphData.adjacency(), args.ASN)
    neigh = graphData[args.ASN]
    mDegNeigh = []
    oneDegNeigh = []
    asn_successor = graphData.successors(args.ASN)
    asn_out_degree = graphData.out_degree(args.ASN)
    asn_in_degree = graphData.in_degree(args.ASN)
    all_successors = nx.dfs_successors(graphData, args.ASN)
    print("In-Degree of AS %s is %s\n" %(args.ASN,asn_in_degree))
    print("Out-Degree of AS %s is %s\n" %(args.ASN,asn_out_degree))
    #print("In-edges of AS %s are %s\n" %(args.ASN, graphData.in_edges(args.ASN)))
    #print("Out-edges of AS %s are %s\n" %(args.ASN, graphData.out_edges(args.ASN)))
    p2c_edges,  p2p_edge = seperateEdges(graphData)
    # Remove ASes with only one neighbour  from neigbours and neigh
    for asn in neigh:
        asn_neigh = graphData[asn]
        asn_out_edges = graphData.out_edges(asn)
        out_edge  = (asn, args.ASN)
        if (len(list(graphData.predecessors(asn))) <= 600) and (args.ASN in graphData.successors(asn)):
        #if (len(asn_neigh) <= 5) and (args.ASN in asn_neigh):
            oneDegNeigh.append(asn)
        else:
            mDegNeigh.append(asn)
    
    if neighbours == neigh:
        #print("Neigbours of AS %s are: %s\n" %(args.ASN, neighbours))
        print("ASN %s has %s neighbours\n" %(args.ASN, len(neighbours)))
    else:
        print("Neigh is not equal to neighbours\n")
        sys.exit(-1)

    #if nx.has_path(graphData, args.ASN, '36040'):
    #    print("Path exists!!!")
    #    all_paths = nx.all_simple_paths(graphData, args.ASN, '36040')

    #for path in all_paths:
    #    print("Path: %s\n" %path)
    #all_paths = nx._all_simple_paths_graph(graphData, args.ASN, '36040')
    sGraph = createSubgraph(graphData, args.ASN, mDegNeigh)
    #as_tree  = nx.dfs_tree(graphData, source=args.ASN, depth_limit=4)
    #sGraph = nx.DiGraph()
    #for edge in as_tree.edges():
    #    if edge in p2c_edges:
    #        sGraph.add_edge(edge[0], edge[1], relationship='p2c')

    #    if edge in p2p_edge:
    #        sGraph.add_edge(edge[0], edge[1], relationship='p2p')

    print("The number of nodes in subgraph around ASN %s is %s\n" %(args.ASN, sGraph.number_of_nodes()))

    #drawTopoGraph(graphData)
    drawTopoGraph(sGraph)
