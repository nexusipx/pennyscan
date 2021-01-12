
$( "th" ).each(function() {
	var text = $(this).html().trim();
	$(this).addClass(text);
	

});

$("input:checkbox:not(:checked)").each(function() {
    var column = "table ." + $(this).attr("name");
    var columnName = $(this).attr("name");
    var index = -1;

    $(column).hide();

    var thList = $( "th" ).each(function(index){
        if($(this).text().trim() == columnName){
            var subColumns = $("tbody td:nth-child("+(index+1)+")");

            $(subColumns).hide();
        }
    });


});

$("input:checkbox").click(function(){
    var column = "table ." + $(this).attr("name");
    var columnName = $(this).attr("name");
    var index = -1;

    $(column).toggle();
    var thList = $( "th" ).each(function(index){
        if($(this).text().trim() == columnName){
            var subColumns = $("tbody td:nth-child("+(index+1)+")");

            $(subColumns).toggle();
        }
    });


});



$('.toggle').click(function() {
	
    $('.PreviousClose').toggle();
	$('.DayLow').toggle();
	$('.Open').toggle();
	$('.DayHigh').toggle();
	$('.AverageVolume').toggle();
	$('.TargetMeanPrice').toggle();
	$('.RecommendationKey').toggle();
	
	var index = -1;
	
	var thList = $( "th" ).each(function(index){
		var cName = $(this).text().trim();
		
        if(cName == "PreviousClose" || cName == "Open" || cName == "DayLow" || cName == "DayHigh" || cName == "AverageVolume" || cName == "TargetMeanPrice" || cName == "RecommendationKey"){
            var subColumns = $("tbody td:nth-child("+(index+1)+")");

            $(subColumns).toggle();
			index = -1;
        }
    });
});