import mysql.connector
from crossref.restful import Works, Etiquette
from datetime import date

TABLE_RESEARCH_PAPERS = "techtree_researchpapers" 
TABLE_AUTHORS = "techtree_authors"
TABLE_AUTHOR_PAPER_RELATION = "techtree_authorpaperrelation"
TABLE_REFERENCE_RELATION = "techtree_referencerelation"
TABLE_CATEGORY = "techtree_category"
TABLE_CATEGORY_RELATION = "techtree_categoryrelation"
TABLE_CATEGORY_PAPER_RELATION = "techtree_categorypaperrelation"

TABLE_NAME = [TABLE_RESEARCH_PAPERS, TABLE_AUTHORS, TABLE_AUTHOR_PAPER_RELATION, TABLE_REFERENCE_RELATION, TABLE_CATEGORY, TABLE_CATEGORY_RELATION, TABLE_CATEGORY_PAPER_RELATION]
#TABLE_CREATESQL = ["CREATE TABLE IF NOT EXISTS " + TABLE_RESEARCH_PAPERS + " (id INT AUTO_INCREMENT PRIMARY KEY, doi VARCHAR(255) UNIQUE, title TEXT, publishdate DATE)","CREATE TABLE IF NOT EXISTS " + TABLE_AUTHORS + " (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255))","CREATE TABLE IF NOT EXISTS " + TABLE_AUTHOR_PAPER_RELATION + " (id INT AUTO_INCREMENT PRIMARY KEY, authorId INT, researchId INT, FOREIGN KEY (authorId) REFERENCES " + TABLE_AUTHORS + "(id) ON DELETE CASCADE, FOREIGN KEY (researchId) REFERENCES " + TABLE_RESEARCH_PAPERS + "(id) ON DELETE CASCADE)","CREATE TABLE IF NOT EXISTS " + TABLE_REFERENCE_RELATION + " (id INT AUTO_INCREMENT PRIMARY KEY, referencingPaper_id INT, referencedPaper_id INT, FOREIGN KEY (referencingPaper_id) REFERENCES " + TABLE_RESEARCH_PAPERS + "(id), FOREIGN KEY (referencedPaper_id) REFERENCES " + TABLE_RESEARCH_PAPERS + "(id))","CREATE TABLE IF NOT EXISTS " + TABLE_CATEGORY + " (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255) UNIQUE)","CREATE TABLE IF NOT EXISTS " + TABLE_CATEGORY_RELATION + " (id INT AUTO_INCREMENT PRIMARY KEY, catId INT, subCatId INT, FOREIGN KEY (catId) REFERENCES " + TABLE_CATEGORY + " (id) ON DELETE CASCADE, FOREIGN KEY (subCatId) REFERENCES " + TABLE_CATEGORY + " (id) ON DELETE CASCADE)","CREATE TABLE IF NOT EXISTS " + TABLE_CATEGORY_PAPER_RELATION + " (id INT AUTO_INCREMENT PRIMARY KEY, paperId INT, catId INT, FOREIGN KEY (paperId) REFERENCES " + TABLE_RESEARCH_PAPERS + " (id) ON DELETE CASCADE, FOREIGN KEY (catId) REFERENCES " + TABLE_CATEGORY + " (id) ON DELETE CASCADE)"]

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
        else:
            # Otherwise, check integrity? TODO later
            print "table " + TABLE_NAME[i] + " found"
            # TODO: If not formatted properly attempt to fix, otherwise warn
    
    return True

def getCategories(cursor,category):
    if category == None:
        cursor.execute("SELECT * FROM " + TABLE_CATEGORY + " LEFT JOIN " + TABLE_CATEGORY_RELATION + " ON " + TABLE_CATEGORY_RELATION + ".subCatId = " + TABLE_CATEGORY + ".id WHERE " + TABLE_CATEGORY_RELATION + ".subCatId IS NULL")
    else:
        cursor.execute("SELECT * FROM " + TABLE_CATEGORY + " INNER JOIN " + TABLE_CATEGORY_RELATION + " ON " + TABLE_CATEGORY_RELATION + ".subCatId = " + TABLE_CATEGORY + ".id WHERE " + TABLE_CATEGORY_RELATION + ".catId = " + str(category[0]))

    return cursor.fetchall()

def addCategory(cursor,category,lastCategory):
    #Check for category duplication
    #TODO
    #Add category
    sql = "INSERT INTO " + TABLE_CATEGORY + " (name) VALUES ('"+category+"')"
    cursor.execute(sql)
    catId = cursor.lastrowid 

    sql = "INSERT INTO " + TABLE_CATEGORY_RELATION + " (catId,subCatId) VALUES (%s,%s)"
    sqlvars = (lastCategory[0], catId)
    cursor.execute(sql,sqlvars)

    return catId

def addToCategory(cursor,paper,category):
    
    sql = "INSERT INTO " + TABLE_CATEGORY_PAPER_RELATION + " (paperId, catId) VALUES (%s,%s)"
    sqlvars = (paper,category)
    cursor.execute(sql,sqlvars)
    print category

def categorizePapers(sql, cursor):
    #1) Iterate through papers, check if entries already exist for the paper (to prevent duplicates) using LEFT JOIN + IS NULL
    #2) Show Prompt with title of article, ask what category it is in - allow entrance of new categories
    #3) If subcategories are available continue prompting
    returnId = -1
    today = str(date.today())
    cursor.execute("SELECT * FROM " + TABLE_RESEARCH_PAPERS + " LEFT JOIN " + TABLE_CATEGORY_PAPER_RELATION + " ON " + TABLE_RESEARCH_PAPERS + ".id = " + TABLE_CATEGORY_PAPER_RELATION + ".paperId WHERE " + TABLE_CATEGORY_PAPER_RELATION + ".paperId IS NULL AND " + TABLE_RESEARCH_PAPERS + ".publishdate <= '" + today + "' ORDER BY " + TABLE_RESEARCH_PAPERS + ".publishdate DESC")
    
    papersToProcess = cursor.fetchall() 
    for entry in papersToProcess:
        print "https://doi.org/" + entry[1] + " - " + entry[2] + " - " + entry[6] + " - " + "{:%Y-%m-%d}".format(entry[3])
        print entry[5]
        print entry[4]
        # Get category options
        categories = getCategories(cursor,None)
        lastCategory = 0
        while categories != None:
            print "Select category:"
            print "-2: Skip"
            print "-1: This is the final category."
            for i in xrange(len(categories)):
                print str(i) + ": " + str(categories[i])
            print "Any text entry will specify a new category."


            #Wait for input from user
            selection = raw_input("Selection: ")
            try:
                selection = int(selection)
                if selection < 0 or selection >= len(categories):
                    # SET THIS CATEGORY AS THE INSTANCE
                    #Add paper here
                    print entry
                    if (selection == -1):
                        addToCategory(cursor, entry[0],lastCategory[0])
                    categories = None
                else:
                    category = categories[selection]
                    lastCategory = category
                    print "You selected:"
                    print category
                    categories = getCategories(cursor,category)
            except ValueError:
                #Create a new category
                thisCategory = addCategory(cursor,selection,lastCategory)  
                categories = getCategories(cursor,lastCategory)

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
    
    categorizePapers(sql,cursor)
     
    # Commit any changes after all transactions completed
    sql.commit()

if __name__ == "__main__":
    main()
    
