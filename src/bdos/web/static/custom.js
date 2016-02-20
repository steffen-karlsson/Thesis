/*
 * Created by Steffen Karlsson on 02-20-2016
 * Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.
 */

$(document).ready(function() {
    addDropDownListener("#query");
    addDropDownListener("#registry-name");

    adjustWidthBySelf("#query");
    adjustWidthBySelf("#registry-name");

    var ndDropdown = $("#new-dataset-dropdown");
    var width = ndDropdown.outerWidth(true);
    ndDropdown.outerWidth(0);
    adjustWidth("#remove-dataset", "#new-dataset");

    $.getJSON( "/register_implemented_datasets", function( data ) {
        $.each( data, function( key, val ) {
            console.log(val);
            $("#dataset-dropdown-menu").append("<li value=\"" + val + "\" id=\"dataset-first\"><a href=\"#\">"
                + key + " </a></li>");

            $("#new-dataset-dropdown-menu").append("<li value=\"" + val + "\" id=\"new-dataset-first\"><a href=\"#\">"
                + val.substring(val.lastIndexOf(".") + 1) + " </a></li>");
        });
        addDropDownListener("#dataset", function(value) {
            window.dataset = value;
        });
        window.dataset = $("#dataset-first").attr("value");

        addDropDownListener("#new-dataset", function(value) {
            console.log(">> " + value);
        });
        ndDropdown.outerWidth(width).css("display", "inline");
        adjustWidthBySelf("#new-dataset");
    });
});

function addDropDownListener(label, valueCallback) {
    $(label + "-dropdown-selection").text($(label + "-first").text())

    $(label + "-dropdown-menu li a").click(function(){
        var selText = $(this).text();
        $(label + "-dropdown-selection").text(selText + " ");
        $(label + "-dropdown-selection").val(selText + " ");
        adjustWidthBySelf(label);

        if (valueCallback !== null)
            valueCallback($(this).parent().attr("value"));
    });
}

function adjustWidthBySelf(label) {
    adjustWidth(label, label)
}

function adjustWidth(toLabel, fromLabel) {
    $(toLabel).width($(".page-header").width()
        - $(fromLabel + "-submit").outerWidth(true)
        - $(fromLabel + "-dropdown").outerWidth(true)
        - ($(fromLabel).outerWidth(true) - $(fromLabel).innerWidth())
        - 30);
}
