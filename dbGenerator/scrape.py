import mysql.connector
from crossref.restful import Works, Etiquette
from datetime import date
import urllib2
import ssl
import re

TABLE_RESEARCH_PAPERS = "techtree_researchpapers" 
TABLE_AUTHORS = "techtree_authors"
TABLE_AUTHOR_PAPER_RELATION = "techtree_authorpaperrelation"
TABLE_REFERENCE_RELATION = "techtree_referencerelation"
TABLE_CATEGORY = "techtree_category"
TABLE_CATEGORY_RELATION = "techtree_categoryrelation"
TABLE_CATEGORY_PAPER_RELATION = "techtree_categorypaperrelation"

TABLE_NAME = [TABLE_RESEARCH_PAPERS, TABLE_AUTHORS, TABLE_AUTHOR_PAPER_RELATION, TABLE_REFERENCE_RELATION, TABLE_CATEGORY, TABLE_CATEGORY_RELATION, TABLE_CATEGORY_PAPER_RELATION]
TABLE_CREATESQL = ["CREATE TABLE IF NOT EXISTS " + TABLE_RESEARCH_PAPERS + " (id INT AUTO_INCREMENT PRIMARY KEY, doi VARCHAR(255) UNIQUE, title TEXT, publishdate DATE, abstract TEXT, rawsubject TEXT, journal TEXT)","CREATE TABLE IF NOT EXISTS " + TABLE_AUTHORS + " (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255))","CREATE TABLE IF NOT EXISTS " + TABLE_AUTHOR_PAPER_RELATION + " (id INT AUTO_INCREMENT PRIMARY KEY, authorId INT, researchId INT, FOREIGN KEY (authorId) REFERENCES " + TABLE_AUTHORS + "(id) ON DELETE CASCADE, FOREIGN KEY (researchId) REFERENCES " + TABLE_RESEARCH_PAPERS + "(id) ON DELETE CASCADE)","CREATE TABLE IF NOT EXISTS " + TABLE_REFERENCE_RELATION + " (id INT AUTO_INCREMENT PRIMARY KEY, referencingPaper_id INT, referencedPaper_id INT, FOREIGN KEY (referencingPaper_id) REFERENCES " + TABLE_RESEARCH_PAPERS + "(id), FOREIGN KEY (referencedPaper_id) REFERENCES " + TABLE_RESEARCH_PAPERS + "(id))","CREATE TABLE IF NOT EXISTS " + TABLE_CATEGORY + " (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255))","CREATE TABLE IF NOT EXISTS " + TABLE_CATEGORY_RELATION + " (id INT AUTO_INCREMENT PRIMARY KEY, catId INT, subCatId INT, FOREIGN KEY (catId) REFERENCES " + TABLE_CATEGORY + " (id) ON DELETE CASCADE, FOREIGN KEY (subCatId) REFERENCES " + TABLE_CATEGORY + " (id) ON DELETE CASCADE)","CREATE TABLE IF NOT EXISTS " + TABLE_CATEGORY_PAPER_RELATION + " (id INT AUTO_INCREMENT PRIMARY KEY, paperId INT, catId INT, FOREIGN KEY (paperId) REFERENCES " + TABLE_RESEARCH_PAPERS + " (id) ON DELETE CASCADE, FOREIGN KEY (catId) REFERENCES " + TABLE_CATEGORY + " (id) ON DELETE CASCADE)"]

def connect():
    sql = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="12345678",
        auth_plugin="caching_sha2_password",
        database="articlenetwork"
        )
    return sql

def checkTables(cursor):
    # Check if each table exists
    cursor.execute("SHOW TABLES")
    tableExists = [False]*len(TABLE_NAME)
    for table in cursor:
        for i in xrange(len(TABLE_NAME)):
            if table[0] == TABLE_NAME[i]:
                tableExists[i] = True

    for i in xrange(len(TABLE_NAME)):
        if tableExists[i] == False:
            # If table doesn't exist, create a new one
            print "creating table " + TABLE_NAME[i]
            cursor.execute(TABLE_CREATESQL[i])

            #If table is the category table, preformat with 4 categories: Natural Science, Social Science, Formal Science, Applied Science
            if (TABLE_NAME[i] == TABLE_CATEGORY):
                sql = "INSERT INTO " + TABLE_CATEGORY + " (name) VALUES ("
                sqlvars = [("'Natural Science'"),("'Social Science'"),("'Formal Science'"),("'Applied Science'")]
                for j in xrange(len(sqlvars)):
                    cursor.execute(sql + sqlvars[j] + ")")
                
        else:
            # Otherwise, check integrity? TODO later
            print "table " + TABLE_NAME[i] + " found"
            # TODO: If not formatted properly attempt to fix, otherwise warn
             
    return True

def isInTable(cursor, item):
    cursor.execute("SELECT * FROM " + TABLE_RESEARCH_PAPERS)
    result = cursor.fetchall()
    
    inDatabase = False
    rowId = -1
    for row in result:
        if 'DOI' in item:
            if row[1] == item['DOI']:
                inDatabase = True
                rowId = row[0]
        elif 'doi' in item:
            if row[1] == item['doi']:
                inDatabase = True
                rowId = row[0]

    return (inDatabase, rowId)

def getAbstract(htmlContent):
    sampleString = "This email address is being protected from spambots. You need JavaScript enabled to view it." #THIS IS A HACK
    hopefullyAbstract = ""
    maxLength = 0
    m = re.findall('>[A-Za-z0-9 (){}\[\]\.\,!\?&;:\"\'\/\-=%]*<',htmlContent,re.UNICODE)
    for group in m:
        if len(group) > maxLength:
            if len(re.findall('\[[0-9]\]',group)) == 0:
                hopefullyAbstract = group[1:-1]
                maxLength = len(group)
    
    if len(hopefullyAbstract) <= len(sampleString):
        hopefullyAbstract = ""
    return hopefullyAbstract

def addToResearchTable(cursor, item):
    sql = "INSERT INTO " + TABLE_RESEARCH_PAPERS + " (doi, title, publishdate,abstract,rawsubject,journal) VALUES (%s,%s,%s,%s,%s,%s)"
    doi = ""
    title = ""
    publishdate = ""
    abstract = ""
    rawsubject = ""
    journal = ""

    if 'DOI' in item:
        doi = item['DOI']
    if 'title' in item:
        if len(item['title']) > 0:
            title = item['title'][0]
            #TODO: ADD WAY TO SCRAPE ABSTRACT FROM DOI URL
    
    #Publishing date
    datearray = []
    if 'issued' in item and 'date-parts' in item['issued'] and item['issued']['date-parts'][0][0] != None:
        datearray.append(item['issued']['date-parts'][0])
    if 'published-print' in item and 'date-parts' in item['published-print'] and item['published-print']['date-parts'][0][0] != None:
        datearray.append(item['published-print']['date-parts'][0])
    if 'start' in item and 'date-parts' in item['start'] and item['start']['date-parts'][0][0] != None:
        datearray.append(item['start']['date-parts'][0])
    if 'created' in item and 'date-parts' in item['created'] and item['created']['date-parts'][0][0] != None:
        datearray.append(item['created']['date-parts'][0])
    if len(datearray) == 0:
        print "DATE NOT FOUND"
        print item

    # Format date array into string
    year = 3000
    month = 12
    day = 12
    for i in xrange(len(datearray)):
        if len(datearray[i]) >= 1 and datearray[i][0] != None:
            extractYear = datearray[i][0]
            extractMonth = 1
            extractDay = 1
            if (len(datearray[i]) >= 2 and datearray[i][1] != None):
                extractMonth = datearray[i][1]
            if (len(datearray[i]) >= 3 and datearray[i][2] != None):
                extractDay = datearray[i][2]
                
            if extractYear+extractMonth/12+extractDay/365 <= year+month/12+day/365:
                year = extractYear #YEAR
                month = extractMonth #MONTH
                day = extractDay #DAY
        else:
            print "Error"
            print item
    publishdate = str(year) + "-" + str(month) + "-" + str(day)
    
    # Publishing journal
    if "container-title" in item and len(item['container-title']) > 0:
        journal = item['container-title'][0]
   
    # Raw Subject
    if "subject" in item and len(item['subject']) > 0:
        rawsubject = item['subject'][0]

    # Abstract
    url = "https://doi.org/"+doi
    try:
        context = ssl._create_unverified_context()
        response = urllib2.urlopen(url,context=context,timeout=60) #Open URL
        page = response.read() #Copy HTML into 'page'
        abstract = getAbstract(page)
        #FOR DEBUGGING
        #text= raw_input("WAITING")
        #if (text == "?"):
        #    print page
    except IOError:
        print "Could not connect to " + url

    #Fix encoding errors before entering into database
    title = title.encode('utf-8',errors='replace')
    abstract = abstract.encode('utf-8',errors='replace')
    rawsubject = rawsubject.encode('utf-8',errors='replace')
    journal = journal.encode('utf-8',errors='replace')

    sqlvars = (doi,title,publishdate,abstract,rawsubject,journal)
    cursor.execute(sql,sqlvars)
    return cursor.lastrowid

def addToReferenceTable(cursor, referencingId, referencedId):
    sql = "INSERT INTO " + TABLE_REFERENCE_RELATION + " (referencingPaper_id, referencedPaper_id) VALUES (%s,%s)"
    sqlvars = (referencingId,referencedId)
    print sqlvars
    cursor.execute(sql,sqlvars)
    return cursor.lastrowid

def recursiveReferenceAdd(sql, cursor, item):
    works = Works()
    
    returnId = -1
    #Check valid item
    if item == None:
        print "Can't find works.doi item"
        return -1

    # Check for duplicates in the database
    tableEntry = isInTable(cursor,item)
    if tableEntry[0] == False:
        returnId = addToResearchTable(cursor,item)
    else:
        print "Got duplicate"
        returnId = tableEntry[1]
        return -1#returnId
        #TODO: Allow a duplicate to check the references and update them

    # Continue checking references recursively 
    #if 'reference' in item:
    #    for i in xrange(len(item['reference'])):
    #        if 'doi' in item['reference'][i]:
    #            if item['reference'][i]['doi'] != None:
    #                returnId2 = recursiveReferenceAdd(sql,cursor,works.doi(item['reference'][i]['doi']))
    #                # Add relations between research papers
    #                if (returnId != -1 and returnId2 != -1):
    #                    addToReferenceTable(cursor, returnId, returnId2)
    #        elif 'DOI' in item['reference'][i]:
    #            if item['reference'][i]['DOI'] != None:
    #                returnId2 = recursiveReferenceAdd(sql,cursor,works.doi(item['reference'][i]['DOI']))
    #                #Add relations between research papers
    #                if (returnId != -1 and returnId2 != -1):
    #                    addToReferenceTable(cursor, returnId, returnId2)

    sql.commit()
    return returnId

def main():
    sql = connect()
    cursor = sql.cursor()

    if checkTables(cursor) == False:
        print "fatal error: tables not verified"
        return
    else:
        print "tables verified"

    # Start scraping and populating data
    # 1) Scraping Entry point: random doi using "sample" - done
    # 2) Back-propagation occurs through citations found in the paper - might have bugs with duplicates
    # 3) When no more unique papers are found, return to step 1 - done
    project = Etiquette('ResearchSub', 'Pre-alpha', 'localhost', 'cphajduk@gmail.com')
    works = Works(etiquette=project)
    for item in works.sort('published').order('desc'):
        recursiveReferenceAdd(sql,cursor, item)
     
    # Commit any changes after all transactions completed
    sql.commit()

if __name__ == "__main__":
    main()
    
