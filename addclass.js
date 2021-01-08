function addClass() { 
    var list = document.getElementsByTagName("table");
    for (let item of list) {
        item.classList.add("sortable");
    }
};

addClass();
