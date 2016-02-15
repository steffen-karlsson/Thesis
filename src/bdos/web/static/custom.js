$(document).ready(function() {
    adjustWidth();

    $("#dropdown-selection").text($("#dropdown-first").text())
    $(".dropdown-menu li a").click(function(){
        var selText = $(this).text();
        $("#dropdown-selection").text(selText + " ");
        $("#dropdown-selection").val(selText + " ");
        adjustWidth();
    });
});

function adjustWidth() {
    $("#query").width($(".page-header").width() - $("#query-submit").outerWidth(true) - $("#query-dropdown").outerWidth(true) - ($("#query").outerWidth(true) - $("#query").innerWidth()) - 25)
}