from graph_tool.all import *
import mysql.connector
import cairo
import math
import random
import json

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


TABLE_RESEARCH_PAPERS = "techtree_researchpapers" 
TABLE_AUTHORS = "techtree_authors"
TABLE_AUTHOR_PAPER_RELATION = "techtree_authorpaperrelation"
TABLE_REFERENCE_RELATION = "techtree_referencerelation"

TABLE_NAME = [TABLE_RESEARCH_PAPERS, TABLE_AUTHORS, TABLE_AUTHOR_PAPER_RELATION, TABLE_REFERENCE_RELATION]

TILE_HEIGHT = 256
TILE_WIDTH = 256

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
        
        #Add Metadata TODO: Turn this into a property map
        metadata[int(vertex)] = {"name":row[2], "doi":row[1], "vertexIndex":int(vertex), "sqlIndex":row[0], "year": row[3].year, "month": row[3].month, "day": row[3].day}
    graph.vertex_properties["metadata"] = metadata

    edgeList = []
    #Load edges (references)
    sql = "SELECT * FROM " + TABLE_REFERENCE_RELATION
    cursor.execute(sql)
    
    for row in cursor:
        edgeList.append(graph.add_edge(vertexList[row[1]-1],vertexList[row[2]-1]))

    #pos = sfdp_layout(graph)
    #pos = testLayout(graph, metadata)
    pos = historicalLayout(graph, metadata)

    return (vertexList, edgeList, pos)

def testLayout(g,metadata):
    MIN_SIZE = 256
    MIN_SPACING = 5
    pos = g.new_vertex_property("vector<double>")
    spacing = 256/g.num_vertices()
    if spacing < MIN_SPACING:
        spacing = MIN_SPACING
    x = spacing
    y = spacing
    
    num = math.sqrt(g.num_vertices())
    for v in g.vertices():
        pos[v] = (x,y)
        x += spacing
        if (x > num*spacing):
            y += spacing
            x = spacing
    return pos

def historicalLayout(g,metadata):
    MIN_SIZE = 256
    MIN_SPACING = 5
    OPTIMAL_SPACING = 20
    HISTORICAL_OFFSET = 1800
    pos = g.new_vertex_property("vector<double>")
    spacing = 256/g.num_vertices()
    if spacing < MIN_SPACING:
        spacing = MIN_SPACING
    x = spacing
    y = spacing
   
    for v in g.vertices():
        x = (metadata[v]['year'] + metadata[v]['month']/12.0 + metadata[v]['day']/365.0 - HISTORICAL_OFFSET)*5
        #Assign random y
        y = random.randint(0,512)
        pos[v] = (x,y)


    # Iterate Y-axis force directed layout
    DISTANCE = 100
    k = 1
    q = 1 
    for i in xrange(66):
        print i
        for v in g.vertices():
            x1 = pos[v][0]
            y1 = pos[v][1]
            for v2 in g.vertices():
                x2 = pos[v2][0]
                y2 = pos[v2][1]

                attraction = 0
                repulsion = 0
                if (math.fabs(x1 - x2) <= DISTANCE and v != v2):
                    distance = math.sqrt((x1-x2)**2+(y1-y2)**2)
                    if distance < 1e-20:
                        repulsion = q 
                    else:
                        repulsion = q/(distance**2)
                if v2 in g.get_out_neighbours(v) or v2 in g.get_in_neighbours(v):
                    attraction = k*(distance - OPTIMAL_SPACING)
                #Positive dY
                if y1 > y2:
                    y1 -= attraction - repulsion
                elif y1 < y2:
                    y1 += attraction - repulsion
                else:
                    y1 = y1 + 1
                if (y1 < 0):
                    y1 = 0
                elif y1 > 10000:
                    y1 = 10000
                pos[v] = (x1,y1)
    for v in g.vertices():
        print pos[v]
    return pos


def historicalLayout2(g,metadata):
    MIN_SIZE = 256
    MIN_SPACING = 5
    OPTIMAL_SPACING = 20
    HISTORICAL_OFFSET = 1800
    pos = g.new_vertex_property("vector<double>")
    spacing = 256/g.num_vertices()
    if spacing < MIN_SPACING:
        spacing = MIN_SPACING
    x = spacing
    y = spacing
   
    for v in g.vertices():
        x = (metadata[v]['year'] + metadata[v]['month']/12.0 + metadata[v]['day']/365.0 - HISTORICAL_OFFSET)*20
        #Assign random y
        y = random.randint(0,512)
        pos[v] = (x,y)


    # Iterate Y-axis force directed layout
    DISTANCE = 10 #Somewhere between 2*k and 20*k
    k = 1
    q = 1
    
    newPos = pos.copy()
    oldPos = pos.copy()

    temperature = 100
    lam = 0.9
    converged = False
    tolerance = 0.1
    i = 0
    while converged == False:
        print "Iteration " + str(i)
        converged = True

        for v in g.vertices():
            oldPos[v] = newPos[v]
   
        yDisplacement = g.new_vertex_property("double")
        xDisplacement = g.new_vertex_property("double")
        for v in g.vertices():
            yDisplacement[v] = 0
            xDisplacement[v] = 0
            for u in g.vertices():
                if u != v:
                    deltaX = pos[u][0] - pos[v][0]
                    deltaY = pos[u][1] - pos[v][1]
                    euclideanDistance = math.sqrt(deltaX**2 + deltaY**2)

                    #For now, all weights are the same
                    w = 1/g.num_vertices()
                    C = 0.2
                    # X-axis is fixed, so only need to calculate Y-axis
                    if euclideanDistance <= DISTANCE and euclideanDistance != 0:
                        rForce = -C*w/euclideanDistance
                        print "rForce: " + str(rForce)
                        sinRatio = math.sin(math.atan2(deltaY,deltaX))
                        cosRatio = 1-sinRatio**2
                        yDisplacement[v] = yDisplacement[v] + rForce*sinRatio
                        xDisplacement[v] = xDisplacement[v] + rForce*cosRatio
                    elif euclideanDistance <= DISTANCE:
                        yDisplacement[v] = yDisplacement[v] - 1
                        xDisplacement[v] = xDisplacement[v] - 1
            for u in g.get_out_neighbours(v):
                deltaX = pos[u][0] - pos[v][0]
                deltaY = pos[u][1] - pos[v][1]
                euclideanDistance = math.sqrt(deltaX**2 + deltaY**2)
                
                aForce = 0.5*k*euclideanDistance**2
                print "aForce: " + str(aForce)
                sinRatio = math.sin(math.atan2(deltaY,deltaX))
                cosRatio = 1-sinRatio**2

                yDisplacement[v] = yDisplacement[v] + aForce*sinRatio
                xDisplacement[v] = xDisplacement[v] + aForce*cosRatio

            # Reposition
            print "PreVal: " + str(yDisplacement[v])

            if xDisplacement[v] > 0:
                if xDisplacement[v] < temperature:
                    newPos[v][0] += xDisplacement[v]
                else:
                    newPos[v][0] += temperature
            else:
                if xDisplacement[v] > -temperature:
                    newPos[v][0] += xDisplacement[v]
                else:
                    newPos[v][0] += -temperature
            if yDisplacement[v] > 0:
                if yDisplacement[v] < temperature:
                    newPos[v][1] += yDisplacement[v]
                else:
                    newPos[v][1] += temperature
            else:
                if yDisplacement[v] > -temperature:
                    newPos[v][1] += yDisplacement[v]
                else:
                    newPos[v][1] += -temperature

            if (math.fabs(newPos[v][1] - oldPos[v][1])) > tolerance:
                converged = False
            print "NewPos: " + str(newPos[v][1]) + " OldPos: " + str(oldPos[v][1]) + " Delta: " + str(newPos[v][1] - oldPos[v][1]) 
        temperature = lam*temperature
        i+=1
    for v in g.vertices():
        print newPos[v]
    return newPos

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
    g.save("tileized.xml.gz")

    #TODO: ADD option to load from file
    
    # Draw
    # REDO: get Canvas_width/height from maximum positions of vertices: max(pos), min(pos)
    xmax = 0
    ymax = 0
    for v in g.vertices():
        if pos[v][0] > xmax:
            xmax = pos[v][0]
        if pos[v][1] > ymax:
            ymax = pos[v][1]
    CANVAS_WIDTH = int(1.1*xmax)  
    CANVAS_HEIGHT = int(1.1*ymax)
    
    z = 0
    #NOTE: -1/+1 added for appropriate margins on generated image
    #Split the canvas into TILE sized chunks
    #for i in xrange(len(vList)):
    #    print pos[i] #FOR DEBUGGING
    #TODO: WILL EVENTUALLY NEED A Z-AXIS scaling solution, for the time being we don't need one
    for x in xrange(0,CANVAS_WIDTH/TILE_WIDTH+1):
        for y in xrange(0,CANVAS_HEIGHT/TILE_HEIGHT+1):
            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, TILE_WIDTH,TILE_HEIGHT) #Canvas W,H
            context = cairo.Context(surface)
            #NOTE: Cairo coordinate system is flipped, (0,0) is the bottom right corner. Here we convert it into standard top-left coordinates
            cairo_draw(g, pos, context, fit_view=(-x*TILE_WIDTH,-y*TILE_HEIGHT,TILE_WIDTH,TILE_HEIGHT)) #X,Y,W,H
            surface.write_to_png("img/"+str(z)+"/"+str(x)+"_"+str(y)+".png")
            
            #Sort out only position and metadata relevant to each tile
            
            #Split pos Property Map into X and Y components seperately for future comparison
            posX = g.new_vertex_property("double")
            posY = g.new_vertex_property("double")
            for v in g.vertices():
                posX[v] = pos[v][0]
                posY[v] = pos[v][1]

            data = []
            rngX = g.new_vertex_property("double")
            rngX[0] = (x)*TILE_WIDTH
            rngX[1] = (x+1)*TILE_WIDTH
            tileVerticesX = find_vertex_range(g,posX,rngX)

            rngY = g.new_vertex_property("double")
            rngY[0] = (y)*TILE_HEIGHT
            rngY[1] =  (y+1)*TILE_HEIGHT
            tileVerticesY = find_vertex_range(g,posY,rngY)

            for vertex in tileVerticesX:
                if vertex in tileVerticesY:
                    #If it is within the search bounds  
                    #Get Metadata, and add position+metadata to json array
                    data.append({"posX":posX[vertex], "posY":posY[vertex], "metadata":g.vertex_properties['metadata'][vertex]})

            with open("img/"+str(z)+"/"+str(x)+"_"+str(y)+".json",'w') as jsonfile:
                json.dump(data,jsonfile)
            
if __name__ == "__main__":
    main()
