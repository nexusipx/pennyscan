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

addSortableClassToTable();
addStyledTableClassToTable();