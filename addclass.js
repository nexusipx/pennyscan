function addSortableClassToTable() { 
    var list = document.getElementsByTagName("table");
    for (let item of list) {
        item.classList.add("sortable");
    }
};

function addStyledTableClassToTable() {
	var list = document.getElementsByTagName("table");
    for (let item of list) {
        item.classList.add("styled-table");
    }
};


function addTickerLinks(){
	var table = document.getElementsByTagName("table")[0];
	
    for(var i = 1; i < table.rows.length; i++) {
		var firstCol = table.rows[i].cells[0]; 
		var url = 'https://finance.yahoo.com/quote/'+firstCol.innerHTML.trim();
        firstCol.innerHTML = "<a href='"+url+"'/>"+firstCol.innerHTML.toString()+"</a>";
    }
}

addSortableClassToTable();
addStyledTableClassToTable();
addTickerLinks();