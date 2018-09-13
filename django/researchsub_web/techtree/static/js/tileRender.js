$(document).ready(reloadCanvas);
$(window).bind("resize", reloadCanvas);

//Scrolling variables
var tileArray = [];
var clickLayer = document.getElementById("tilediv");
var down = false;
var offsetX = 0;
var offsetY = 0;
var startPosX;
var startPosY;
var canvas;

function reloadCanvas(){
    var w = $(window).width();
    var h = $(window).height();
    canvas = document.getElementById("tilecanvas");
    canvas.width = w;
    canvas.height = h;


    //Load grid array - 256pixel width+height
    var xArray = [];
    for (x = 0; x < w/256; x++){
        var yArray = [];
        for (y = 0; y < h/256; y++){
                //JSON request and get each system
                yArray.push(new Tile(x,y,0));
        }
        xArray.push(yArray);
    }
    tileArray = xArray;
    
    //Onclick/onMove Listeners
    canvas.onmousedown = function(e) {
        lastPosX = e.layerX;
        lastPosY = e.layerY;
        down = true;
    };
    canvas.onmouseup = function() {
        down = false;  
    };

    canvas.onmousemove = function(e) {
        var tooltip = document.getElementById('tooltip');
        if (down == true){
            tooltip.style.display = "none";
            dX = e.layerX - lastPosX;
            dY = e.layerY - lastPosY;
            lastPosX = e.layerX;
            lastPosY = e.layerY;
            //Update initial tiles
            for (x = 0; x < tileArray.length; x++){
                for (y = 0; y < tileArray[x].length; y++){
                    tileArray[x][y].moveTile(dX, dY);
                }
            }
            //Update global "WORLD" offest
            offsetX += dX;
            offsetY += dY;
            
            //Load/Unload new tiles TODO: Unload
            var visible = getVisibleTiles(canvas.width, canvas.height, 256,256);
            for (i=0; i < visible.length;i++){
                x = visible[i][0]; y = visible[i][1];
                if (x >= 0 && y >= 0){
                    if (x > tileArray.length - 1){
                        tileArray.push([]);
                    }
                    if (tileArray[x].length - 1 < y){
                        tileArray[x].push(new Tile(x,y,0));
                    }
                }
            }
        }
        else{
            //If the mouse button isn't down, check for mouse overlap with any of the points
            MIN_SPACING = 5/2;
            //Spacing is calibrated for any offset from movements
            var relativeX = e.layerX - offsetX;
            var relativeY = e.layerY - offsetY;
            //First isolate the correct tile, to avoid iterating over all tiles, also ensure tile exists
            if (typeof tileArray[Math.floor(relativeX/256)] == 'undefined'){
                return;
            }            
            if (typeof tileArray[Math.floor(relativeX/256)][Math.floor(relativeY/256)] == 'undefined'){
                return;
            }            
            if (typeof tileArray[Math.floor(relativeX/256)][Math.floor(relativeY/256)].tileData == 'undefined'){
                return;
            }            
            //Find if mouse is close enough to any points
            var popupShown = false;

            var searchArr = tileArray[Math.floor(relativeX/256)][Math.floor(relativeY/256)].tileData;
            for (i=0; i < searchArr.length; i++) {
                if (Math.abs(searchArr[i].posX-relativeX) < MIN_SPACING){
                    if (Math.abs(searchArr[i].posY-relativeY) < MIN_SPACING){
                        //Show data in a popup
                        tooltip.style.top = (e.layerY-20)+ 'px';
                        tooltip.style.left = (e.layerX+20)+ 'px';
                        tooltip.style.width = "20em";
                        tooltip.style.display = "block";
                        tooltip.innerHTML = "<a style='color:black;text-decoration:none;' href=http://doi.org/"+searchArr[i].metadata.doi+">"+ searchArr[i].metadata.name + "</a><br /><a href=http://doi.org/"+searchArr[i].metadata.doi+" />" + searchArr[i].metadata.doi + "</a>";
                        popupShown = true;
                    }
                }
            }
            if (popupShown == false){
                //Hide any prexisting popups
                //tooltip.style.display = "none";
                //setTimeout(function(){tooltip.style.display = "none";},2000);
            }
        }
    };
}


function getVisibleTiles(canvasWidth,canvasHeight, tileWidth, tileHeight){
    visible = [];
    for (x=-offsetX/tileWidth; x < (canvasWidth-offsetX)/tileWidth; x++){
        for (y=-offsetY/tileHeight; y < (canvasHeight-offsetY)/tileHeight; y++){
           visible.push([Math.floor(x),Math.floor(y)]); 
        }
    }
    return visible;
}


/*
WORLD X,Y,Z [0-W_world, 0-H_world, 0-Depends on detail, starting with 5 levels]
TILE X,Y [0-W_world/255,0-H_world/255]
INNERTILE X,Y [0-255, 0-255]
*/

function Tile(tileX, tileY , tileZ){
    this.tileX = tileX; this.tileY = tileY; this.tileZ = tileZ;
    this.width = 256; this.height = 256;
    var posX = tileX*this.width + offsetX;
    var posY = tileY*this.height + offsetY;
    var context = document.getElementById('tilecanvas').getContext('2d');
    var initialLoad = false;

     //JSON request
    var xhr = new XMLHttpRequest(); // a new request
    var url = "/tile?x="+tileX+"&y="+tileY+"&z="+tileZ;
    xhr.open("GET",url);
    
    var img = new Image();
    var tileContext = this;
    xhr.onreadystatechange = function(){
        var DONE = 4; // readyState 4 means the request is done.
        var OK = 200; // status 200 is a successful return.
        if (xhr.readyState === DONE) {
            if (xhr.status === OK) {
                var tile = JSON.parse(xhr.responseText);
                //Iterate over array and place images from each JSON request
                img.onload = function(){
                    context.drawImage(img,posX,posY,this.width,this.height);
                    tileContext.initialLoad = true;
                }
                console.log(tileX);
                console.log(tileY);
                img.src = "data:image/png;base64," + tile.image;
                tileContext.tileData = tile.metadata;
            } else {
                    console.log('Error: ' + xhr.status); // An error occurred during the request.
            }
        }
    }
    xhr.send(null);
    this.img = img;
    this.context = context;
    this.posX = posX;
    this.posY = posY;
}

Tile.prototype.moveTile = function(dx,dy){
    var clearX = this.posX; var clearY = this.posY;
    if (this.posX < 0){
        clearX = 0;
    }
    if (this.posY < 0){
        clearY = 0;
    }
    this.context.clearRect(clearX,clearY,clearX + this.width, clearY + this.height);
    this.posX += dx;
    this.posY += dy;
    this.context.drawImage(this.img,this.posX,this.posY,this.width,this.height);
};
