// Adobe ImageReady Preload Script
// modified, of course, to allow for a base directory

var baseDir = "../static/images/";

$(document).ready(function() {
    $('#example').DataTable();
} );

function newImage(arg) {
	if (document.images) {
		rslt = new Image();
		rslt.src = arg;
		return rslt;
	}
}

function changeImages(name, src) {
	if (document.images && (preloadFlag == true)) {
		document[name].src = baseDir + src;
	}
}

var preloadFlag = false;
function preloadImages() {
	if (document.images) {
		prospective_link_over = newImage(baseDir + "prospective_link-over.gif");
		current_link_over = newImage(baseDir + "current_link-over.gif");
		faculty_link_over = newImage(baseDir + "faculty_link-over.gif");
		research_link_over = newImage(baseDir + "research_link-over.gif");
		resources_link_over = newImage(baseDir + "resources_link-over.gif");
		preloadFlag = true;
	}
}
