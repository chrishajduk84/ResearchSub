# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.
class ResearchPapers(models.Model):
    doi = models.CharField(max_length=255,unique=True)
    title = models.TextField()
    publishdate = models.DateField()
    abstract = models.TextField()
    rawsubject = models.TextField()
    journal = models.TextField()

class ReferenceRelation(models.Model):
    referencingPaper = models.ForeignKey('ResearchPapers', on_delete=models.CASCADE, related_name="+") 
    referencedPaper = models.ForeignKey('ResearchPapers', on_delete=models.CASCADE, related_name="+") 

class Category(models.Model):
    name = models.CharField(max_length=255)

class CategoryRelation(models.Model):
    catId = models.ForeignKey('Category', on_delete=models.CASCADE, related_name="+")
    subCatId = models.ForeignKey('Category', on_delete=models.CASCADE, related_name="+")

class CategoryPaperRelation(models.Model):
    paperId = models.ForeignKey('ResearchPapers',on_delete=models.CASCADE, related_name="+") 
    catId = models.ForeignKey('Category',on_delete=models.CASCADE, related_name="+")
