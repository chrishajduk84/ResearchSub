# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import HttpResponse, JsonResponse, Http404
from django.db import connection

from techtree.models import ResearchPapers,ReferenceRelation, Category, CategoryRelation, CategoryPaperRelation 

import json
import base64
import os
import StringIO
import mysql.connector

# Create your views here.

class HomePageView(TemplateView):
    def get(self, request, **kwargs):
        return render(request, 'gindex.html', context=None)
    

class GraphView(TemplateView):
    
    def get(self, request, **kwargs):     
        period = request.GET.get('period')
        catId = request.GET.get('catId')
        
        #Default is 0
        if catId == None or catId == "0": #Do more checks (is Number? is day, week, month, year?)
            catId = 0
        if period == None or period == "0":
            period = "day"

        #Using the model and 'catId', get SQL list of categories
        raw_categories = ()
        categories = []
        currentCategoryName = ""
        print "PRE CONNECTION"
        with connection.cursor() as cursor:
            if catId == 0:
                cursor.execute("SELECT * FROM techtree_category LEFT JOIN techtree_categoryrelation ON techtree_category.id=techtree_categoryrelation.subCatId WHERE techtree_categoryrelation.catId IS NULL")
                currentCategoryName = "Science"
            else:
                cursor.execute("SELECT name FROM techtree_category WHERE id=%s",[catId])
                currentCategoryName = str(cursor.fetchone()[0])
                cursor.execute("SELECT * FROM techtree_category LEFT JOIN techtree_categoryrelation ON techtree_category.id=techtree_categoryrelation.subCatId WHERE techtree_categoryrelation.catId=%s",[catId])
            raw_categories = cursor.fetchall()
            print "POST CONNECTION 1"
            #Calculate total count - iterate through each category and generate a JSON object
            papers = self.paperQuery(catId,cursor)
            for category in raw_categories:
                subCatPapers = self.paperQuery(category[0], cursor) #Fix this later so it happens outside of the for loop TODO
                #papers += subCatPapers
                categories.append({'name':category[1],'catId':category[0],'subCatPapers':subCatPapers,'papersCount':len(subCatPapers), 'period':period})
            count = len(categories)
            
        response_data = {'name':currentCategoryName,'period':period,'categories':categories,'catId':catId,'count':count, 'papers':papers}
        return JsonResponse(response_data)

    def paperQuery(self, category, cursor):
        papers = []
        #Check current category for papers
        catArray = [category]
        catArray += self.getSubcategories(category,cursor)
        catString = str(catArray[0])
        for i in xrange(1,len(catArray)):
            catString += "," + str(catArray[i])
        cursor.execute("SELECT * FROM techtree_researchpapers INNER JOIN techtree_categorypaperrelation ON techtree_researchpapers.id = techtree_categorypaperrelation.paperId WHERE techtree_categorypaperrelation.catId in ("+catString+") ORDER BY techtree_researchpapers.publishdate DESC")
        papers = cursor.fetchall()
        return papers

    def getSubcategories(self, category, cursor):
        catArray = []
        #Find related categories and recursively count them
        if category == 0:
            cursor.execute("SELECT * FROM techtree_category LEFT JOIN techtree_categoryrelation ON techtree_category.id = techtree_categoryrelation.subCatId WHERE techtree_categoryrelation.catId IS NULL")
        else:
            cursor.execute("SELECT * FROM techtree_category LEFT JOIN techtree_categoryrelation ON techtree_category.id = techtree_categoryrelation.subCatId WHERE techtree_categoryrelation.catId = "+str(category))
        subCategories = cursor.fetchall()
        for subCategory in subCategories:
            catArray.append(subCategory[0])
            catArray += self.getSubcategories(subCategory[0],cursor)
        return catArray
