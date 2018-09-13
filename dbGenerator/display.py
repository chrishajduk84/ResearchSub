from graph_tool.all import *
import mysql.connector

# Load data
#g = gt.collection.data["polblogs"]
# Setup graph-view - label largest component
#g = gt.GraphView(g, vfilt=gt.label_largest_component(gt.GraphView(g, directed=False)))
# What does this do?
#state = gt.BlockState(g, B=g.num_vertices(), deg_corr=True)
# What does this do?
#state = gt.multilevel_minimize(state, B=2)
# Draw the graph at prearranged positions, send output to pdf file
#gt.graph_draw(g, pos=g.vp["pos"], vertex_fill_color=state.get_blocks(), output="polblogs_agg.pdf")


TABLE_RESEARCH_PAPERS = "researchpapers" 
TABLE_AUTHORS = "authors"
TABLE_AUTHOR_PAPER_RELATION = "authorpaperrelation"
TABLE_REFERENCE_RELATION = "referencerelation"

TABLE_NAME = [TABLE_RESEARCH_PAPERS, TABLE_AUTHORS, TABLE_AUTHOR_PAPER_RELATION, TABLE_REFERENCE_RELATION]

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

def loadPapers(cursor, graph):
    #Load vertices (papers)
    sql = "SELECT * FROM " + TABLE_RESEARCH_PAPERS
    cursor.execute(sql)
    
    vertexList = []
    metadata = graph.new_vertex_property("object")
    for row in cursor:
        #Add Vertex
        vertex = graph.add_vertex()
        vertexList.append(vertex)
        
        #Add Metadata
        metadata[int(vertex)] = {"name":row[2], "doi":row[1], "vertexIndex":int(vertex), "sqlIndex":row[0], "date": row[0]}
    graph.vertex_properties["article"] = metadata

    edgeList = []
    #Load edges (references)
    sql = "SELECT * FROM " + TABLE_REFERENCE_RELATION
    cursor.execute(sql)
    
    for row in cursor:
        edgeList.append(graph.add_edge(vertexList[row[1]-1],vertexList[row[2]-1]))

    return (vertexList, edgeList, 0)#vertexPos)

def main():
    sql = connect()
    cursor = sql.cursor()

    if checkTables(cursor) == False:
        print "fatal error: tables not verified"
        return
    else:
        print "tables verified"

    g = Graph(directed=False)
    (vList, eList, pos) = loadPapers(cursor, g)
    
    # Save
    g.save("test.xml.gz")

    # Draw
    graph_draw(g, vertex_font_size=20, output_size=(8000,8000), output="test.png") #vertex_text=g.vertex_index,
     

if __name__ == "__main__":
    main()
