# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import HttpResponse, JsonResponse, Http404

from techtree.models import ResearchPapers,ReferenceRelation 

import json
import base64
import os
import StringIO
import cairo
import mysql.connector
from graph_tool.all import *

# Create your views here.

class HomePageView(TemplateView):
    def get(self, request, **kwargs):
        return render(request, 'gindex.html', context=None)
    
class TileView(TemplateView):
    TILE_WIDTH = 256
    TILE_HEIGHT = 256

    def get(self, request, **kwargs):
        x = request.GET.get('x')
        y = request.GET.get('y')
        z = request.GET.get('z')
        if (x == None or y == None):
            print "TODO: Add proper error handling here"
            return
        #surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, TileView.TILE_WIDTH, TileView.TILE_HEIGHT) #Canvas W,H
        #context = cairo.Context(surface)
        # Draw something ...graph-tool here
         
        #g = Graph(directed=False)
        #(vList, eList, pos) = self.loadPapers(g)
        #cairo_draw(g, pos, context, fit_view=(256,256,TileView.TILE_WIDTH,TileView.TILE_HEIGHT)) #X,Y,W,H
        #response_data = {}
        #image = StringIO.StringIO()
        #surface.write_to_png(image)
        #response_data['image'] = base64.b64encode(image.getvalue())
        #response_data['article'] = g.vp.article
        response_data = {}
        module_dir = os.path.dirname(__file__)  # get current directory
        image_path = os.path.join(module_dir, "static/img/"+z+"/"+x+"_"+y+".png")
        json_path = os.path.join(module_dir, "static/img/"+z+"/"+x+"_"+y+".json")
        
        if os.path.exists(image_path) == False or os.path.exists(json_path) == False:
            raise Http404()
        with open(image_path,"rb") as image:
            response_data['image'] = base64.b64encode(image.read())
            # Read JSON file, add metadata (only for current tile)
            with open(json_path, "rb") as metadata:
                response_data['metadata'] = json.load(metadata)
        return JsonResponse(response_data)

    def loadPapers(self, graph):
        #Load vertices (papers)
        vertexList = []
        metadata = graph.new_vertex_property("object")
        for row in ResearchPapers.objects.all().iterator():
            #Add Vertex
            vertex = graph.add_vertex()
            vertexList.append(vertex)
            #Add Metadata
            metadata[int(vertex)] = {"name":row.title, "doi":row.doi, "vertexIndex":int(vertex), "sqlIndex":row.id, "date": row.id}
        graph.vertex_properties["article"] = metadata
         
        edgeList = []
        #Load edges (references)
        for row in ReferenceRelation.objects.all().iterator():
            edgeList.append(graph.add_edge(vertexList[row.referencingPaper.id-1],vertexList[row.referencedPaper.id-1]))
        
        #TODO: GRAPH SHOULD BE PREGENERATED EVERY NIGHT/WEEK
        #TODO: position layout should be determined by branch-tree alorigthm, where X-axis is time
        pos = sfdp_layout(graph)
        print pos
        return (vertexList,edgeList,pos)

class GraphView(TemplateView):
    
    def get(self, request, **kwargs):     
        period = request.GET.get('period')
        catId = request.GET.get('catId')
        
        count = 100
        reponseData = {'period':period,'category':'biology','catId':catId,'count':count}
        return JsonResponse(response_data)
