$(window).load(reloadCanvas);
$(window).bind("resize", reloadCanvas);

//Scrolling variables
var graphLayer;
var down = false;
var sWidth = 0;
var sHeight = 0;
var mTotalWidth = 0;

var enableScroll = false;

function reloadCanvas(){
    sWidth = $(window).width() - document.getElementById("infodiv").offsetWidth;
    sHeight = $(window).height();

    //Clear all content from window before reloading
    graphLayer = document.getElementById("graphdiv");
    graphLayer.innerHTML = "";
    //graphLayer.style.width = sWidth + "px";

    var urlstring = window.location.href;
    var url = new URL(urlstring);
    var catId = url.searchParams.get('catId');
    console.log(catId);
    new Graph(catId);

    //Onclick/onMove Listeners
    graphLayer.onmousedown = function(e) {
        lastPosX = e.layerX;
        lastPosY = e.layerY;
        down = true;
    };
    graphLayer.onmouseup = function() {
        down = false;  
    };

    graphLayer.onmousemove = function(e) {
    };
}


function Graph(catId){
    this.loaded = false;

     //JSON request
    var xhr = new XMLHttpRequest(); // a new request
    if (catId == null){catId = 0;}
    var url = "/graph?catId="+catId;
    xhr.open("GET",url);
    
    var graphContext = this;
    xhr.onreadystatechange = function(){
        var DONE = 4; // readyState 4 means the request is done.
        var OK = 200; // status 200 is a successful return.
        if (xhr.readyState === DONE) {
            if (xhr.status === OK) {
                graphContext.data = JSON.parse(xhr.responseText);
                graphContext.loaded = true;
                graphContext.setLayout(sWidth, sHeight,graphContext.data['categories']);
                document.getElementById("categorylabel").innerHTML = graphContext.data['name'];
                graphContext.showPapers(graphContext.data['papers'])
                for (i=0;i<graphContext.data['categories'].length;i++){
                    graphContext.createElement(i,graphContext.data['categories'][i]);
                }
            } else {
                    console.log('Error: ' + xhr.status); // An error occurred during the request.
            }
        }
    }
    xhr.send(null);
    this.catId = catId;

}

Graph.prototype.setLayout = function(width,height,data){
   console.log(width); 
    //Maximum number of elements
    var count = data.length;
    var hiddenCount = 0;
    if (count > 10){hiddenCount = count - 10;count = 10;enableScroll = true;}
    //Maximum width (don't want one bar to take up the whole screen) TODO
    if (count < 4){count = 4;} 
    
    this.elementWidth = width/count/2;
    this.elementSpacing = width/count/2;
    this.totalWidth = width + hiddenCount*(this.elementWidth + this.elementSpacing);
    mTotalWidth = this.totalWidth; //Set the global variable for onkeydown handling

    //Height
    var maxCount = 0;
    var minCount = height;
    for (i=0;i<data.length;i++){
        if (data[i]['papersCount'] > maxCount){
            maxCount = data[i]['papersCount'];
        }
        if (data[i]['papersCount'] < minCount){
            minCount = data[i]['papersCount'];
        }
    }
    var heightMargin = height*0.4; //50%
    this.scale = (height-heightMargin)/(maxCount);
    this.bottomOffset = (height - maxCount*this.scale)/2;
}

Graph.prototype.createElement = function(i,data){
    //Category
    var category = document.createElement("div");
    category.classList.add("category");
    category.style.width = this.elementWidth + "px";
    category.style.margin = "auto " + this.elementSpacing/2 + "px";
    category.style.bottom = this.bottomOffset +"px";
    //TODO: Center the bars if they don't fill the screen
    category.style.left = i * (this.elementWidth + this.elementSpacing) + "px";
    category.onclick= function(){
        window.location = "?catId="+data['catId']+"&period="+data['period']
    }

    var name = document.createElement("span");
    name.classList.add("categoryname");
    var bar = document.createElement("div");
    bar.classList.add("categorybar");
    bar.style.height = data['papersCount']*this.scale + "px";

    var count = document.createElement("span");
    count.classList.add("categorycount");
    count.style.top = data['papersCount']*this.scale/2 +"px";
    count.style.left = this.elementWidth/2 + "px";

    //Add content
    name.textContent = data['name'];
    count.textContent = data['papersCount']; 

    //Append elements in correct order
    if (parseInt(bar.style.height) > 5){
        bar.appendChild(count);
    }
    category.appendChild(bar);
    category.appendChild(name);
    graphdiv.appendChild(category);
}

Graph.prototype.showPapers = function(papers){
    var papersdiv = document.getElementById("papersdiv");
    for (i=0;i<papers.length;i++){
        var p = document.createElement("div");
        p.classList.add("paper");
        p.innerHTML = "<a href='http://doi.org/"+papers[i][1]+"'>"+papers[i][2]+"</a><br /> DOI: "+papers[i][1]+"<br />"+papers[i][3]+"<br />";

        papersdiv.appendChild(p);
    }
}

document.onkeydown = function(e){
    if (enableScroll == true){
        
        var graphObject = document.getElementById("graphdiv");
        if (graphObject.style.left == ""){
            graphObject.style.left = "0px";
        }
        //Left
        if (e.keyCode == 37){
            if (parseInt(graphObject.style.left) < 0){
                graphObject.style.left = (parseInt(graphObject.style.left) + 30) + "px";
            }
        }
        //Right
        if (e.keyCode == 39){
            if (parseInt(graphObject.style.left) > -(mTotalWidth-sWidth)){
                graphObject.style.left = (parseInt(graphObject.style.left) - 30) + "px";
            }
        }
    }
}
