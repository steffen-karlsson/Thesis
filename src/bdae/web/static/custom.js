/*
 * Created by Steffen Karlsson on 02-20-2016
 * Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.
 */

$(document).ready(function() {
    addDropDownListener("#add-registry-name");

    var ndDropdown = $("#new-dataset-dropdown");
    var width = ndDropdown.outerWidth(true);
    ndDropdown.outerWidth(0);
    adjustWidth("#remove-dataset", "#new-dataset");


    adjustWidthBySelf("#add-registry-name");
    adjustWidth("#remove-registry-name", "#new-dataset");

    $.getJSON( "/register_implemented_datasets", function( data ) {
        $.each( data, function( key, val ) {
            $("#dataset-dropdown-menu").append("<li value=\"" + val + "\" id=\"dataset-first\"><a href=\"#\">"
                + key + " </a></li>");

            $("#new-dataset-dropdown-menu").append("<li value=\"" + val + "\" id=\"new-dataset-first\"><a href=\"#\">"
                + val.substring(val.lastIndexOf(".") + 1) + " </a></li>");
        });
        addDropDownListener("#dataset", function( text ) {
            setDatasetFunctions(text, "operations");
        });
        setDatasetFunctions($("#dataset-first").text(), "operations");

        addDropDownListener("#new-dataset", function( text ) {
            console.log(">> " + text);
        });
        ndDropdown.outerWidth(width).css("display", "inline");
        adjustWidthBySelf("#new-dataset");
    });
});

function setDatasetFunctions(dataset_name, functions_name) {
    window.dataset = dataset_name
    $.getJSON("/get_functions/" + dataset_name + "/" + functions_name, function( data ) {
        $.each( data, function( idx, entry ) {
            $("#query-dropdown-menu").append("<li id=\"query-first\"><a href=\"#\">"
                + entry + " </a></li>");
        });

        addDropDownListener("#query");
        adjustWidthBySelf("#query");
    });
}

function addDropDownListener(label, valueCallback) {
    $(label + "-dropdown-selection").text($(label + "-first").text())

    $(label + "-dropdown-menu li a").click(function(){
        var selText = $(this).text();
        $(label + "-dropdown-selection").text(selText + " ");
        $(label + "-dropdown-selection").val(selText + " ");
        adjustWidthBySelf(label);

        if (valueCallback !== null)
            valueCallback(selText);
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
