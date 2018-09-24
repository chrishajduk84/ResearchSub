import mysql.connector
from crossref.restful import Works, Etiquette
import datetime import date

TABLE_RESEARCH_PAPERS = "techtree_researchpapers" 
TABLE_AUTHORS = "techtree_authors"
TABLE_AUTHOR_PAPER_RELATION = "techtree_authorpaperrelation"
TABLE_REFERENCE_RELATION = "techtree_referencerelation"
TABLE_CATEGORY = "techtree_category"
TABLE_CATEGORY_RELATION = "techtree_categoryrelation"
TABLE_CATEGORY_PAPER_RELATION = "techtree_categorypaperrelation"

TABLE_NAME = [TABLE_RESEARCH_PAPERS, TABLE_AUTHORS, TABLE_AUTHOR_PAPER_RELATION, TABLE_REFERENCE_RELATION, TABLE_CATEGORY, TABLE_CATEGORY_RELATION, TABLE_CATEGORY_PAPER_RELATION]
TABLE_CREATESQL = ["CREATE TABLE IF NOT EXISTS " + TABLE_RESEARCH_PAPERS + " (id INT AUTO_INCREMENT PRIMARY KEY, doi VARCHAR(255) UNIQUE, title TEXT, publishdate DATE)","CREATE TABLE IF NOT EXISTS " + TABLE_AUTHORS + " (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255))","CREATE TABLE IF NOT EXISTS " + TABLE_AUTHOR_PAPER_RELATION + " (id INT AUTO_INCREMENT PRIMARY KEY, authorId INT, researchId INT, FOREIGN KEY (authorId) REFERENCES " + TABLE_AUTHORS + "(id) ON DELETE CASCADE, FOREIGN KEY (researchId) REFERENCES " + TABLE_RESEARCH_PAPERS + "(id) ON DELETE CASCADE)","CREATE TABLE IF NOT EXISTS " + TABLE_REFERENCE_RELATION + " (id INT AUTO_INCREMENT PRIMARY KEY, referencingPaper_id INT, referencedPaper_id INT, FOREIGN KEY (referencingPaper_id) REFERENCES " + TABLE_RESEARCH_PAPERS + "(id), FOREIGN KEY (referencedPaper_id) REFERENCES " + TABLE_RESEARCH_PAPERS + "(id))","CREATE TABLE IF NOT EXISTS " + TABLE_CATEGORY + " (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255) UNIQUE)","CREATE TABLE IF NOT EXISTS " + TABLE_CATEGORY_RELATION + " (id INT AUTO_INCREMENT PRIMARY KEY, catId INT, subCatId INT, FOREIGN KEY (catId) REFERENCES " + TABLE_CATEGORY + " (id) ON DELETE CASCADE, FOREIGN KEY (subCatId) REFERENCES " + TABLE_CATEGORY + " (id) ON DELETE CASCADE)","CREATE TABLE IF NOT EXISTS " + TABLE_CATEGORY_PAPER_RELATION + " (id INT AUTO_INCREMENT PRIMARY KEY, paperId INT, catId INT, FOREIGN KEY (paperId) REFERENCES " + TABLE_RESEARCH_PAPERS + " (id) ON DELETE CASCADE, FOREIGN KEY (catId) REFERENCES " + TABLE_CATEGORY + " (id) ON DELETE CASCADE)"]

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
                sqlvars = [("'Pure Science'"),("'Social Science'"),("'Formal Science'"),("'Applied Science'")]
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

def addToResearchTable(cursor, item):
    sql = "INSERT INTO " + TABLE_RESEARCH_PAPERS + " (doi, title, publishdate) VALUES (%s,%s,%s)"
    doi = ""
    title = ""
    publishdate = ""
    if 'DOI' in item:
        doi = item['DOI']
    if 'title' in item:
        if len(item['title']) > 0:
            title = item['title'][0]
    #TODO: ADD WAY TO SCRAPE ABSTRACT FROM DOI URL
    
    #Publishing date
    datearray = [[]]
    if 'issued' in item and 'date-parts' in item['issued'] and item['issued']['date-parts'][0][0] != None:
        datearray = item['issued']['date-parts']
    elif 'published-print' in item and 'date-parts' in item['published-print'] and item['published-print']['date-parts'][0][0] != None:
        datearray = item['published-print']['date-parts']
    elif 'start' in item and 'date-parts' in item['start'] and item['start']['date-parts'][0][0] != None:
        datearray = item['start']['date-parts']
    elif 'created' in item and 'date-parts' in item['created'] and item['created']['date-parts'][0][0] != None:
    datearray = item['created']['date-parts']
    else:
        print "DATE NOT FOUND"
        print item

    # Format date array into string
    year = "0000"
    month = "01"
    day = "01"
    if datearray[0][0] != None:
        if len(datearray[0]) >= 1:
            year = str(datearray[0][0]) #YEAR
        if len(datearray[0]) >= 2:
            month = str(datearray[0][1]) #MONTH
        if len(datearray[0]) >= 3:
            day = str(datearray[0][2]) #DAY
    else:
        print "Error"
        print item
    publishdate = year + "-" + month + "-" + day
    sqlvars = (doi,title,publishdate)
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
    if 'reference' in item:
        for i in xrange(len(item['reference'])):
            if 'doi' in item['reference'][i]:
                if item['reference'][i]['doi'] != None:
                    returnId2 = recursiveReferenceAdd(sql,cursor,works.doi(item['reference'][i]['doi']))
                    # Add relations between research papers
                    if (returnId != -1 and returnId2 != -1):
                        addToReferenceTable(cursor, returnId, returnId2)
            elif 'DOI' in item['reference'][i]:
                if item['reference'][i]['DOI'] != None:
                    returnId2 = recursiveReferenceAdd(sql,cursor,works.doi(item['reference'][i]['DOI']))
                    #Add relations between research papers
                    if (returnId != -1 and returnId2 != -1):
                        addToReferenceTable(cursor, returnId, returnId2)

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
    
