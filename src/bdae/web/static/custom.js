/*
 * Created by Steffen Karlsson on 02-20-2016
 * Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.
 */

$(document).ready(function() {
    var ndDropdown = $("#new-dataset-dropdown");
    var width = ndDropdown.outerWidth(true);
    ndDropdown.outerWidth(0);

    addDropDownListener("#add-registry-name");
    adjustWidthBySelf("#add-registry-name");

    adjustWidth("#remove-dataset", "#new-dataset");
    adjustWidth("#remove-registry-name", "#new-dataset");

    adjustWidthBySelf("#update-dataset");
    onClickListener("#update-dataset", function () {
        console.log($("#update-dataset").val());
    });

    $.getJSON( "/register_implemented_datasets", function( data ) {
        $.each( data, function( key, val ) {
            $("#dataset-dropdown-menu").append("<li value=\"" + val + "\" id=\"dataset-first\"><a href=\"#\">"
                + key + " </a></li>");

            var element1 = "<li value=\"" + val + "\" id=\"";
            var element2 = "-dataset-first\"><a href=\"#\">" + val.substring(val.lastIndexOf(".") + 1) + " </a></li>";
            $("#new-dataset-dropdown-menu").append(element1 + "new" + element2);
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


        onClickListener("#query", function () {
            callData = { "dataset-name": window.dataset,
                         "function-name": $.trim($("#query-dropdown-button").text()),
                         "query": $("#query").val(),
                         "is-polling": false };

            window.dialog = BootstrapDialog.show( {
                closable: false,
                message: function (dialog) {
                    var $content = $('<div><button class="btn btn-success">Revert button status right now.</button></div>');
                    var $progress = $('<div class="progress"><div class="progress-bar progress-bar-striped active" role="progressbar" aria-valuenow="100" aria-valuemin="0" aria-valuemax="100" style="width: 100%"></div></div>');
                    return $progress;
                },
                title: "Querying"
            });
            pollForQueryResult(callData, 200, 0);
        });
    });
});

function setDatasetFunctions(dataset_name, functions_type) {
    window.dataset = dataset_name
    $.getJSON("/get_functions/" + dataset_name + "/" + functions_type, function( data ) {
        $.each( data, function( idx, entry ) {
            $("#query-dropdown-menu").append("<li id=\"query-first\"><a href=\"#\">"
                + entry + " </a></li>");
        });

        addDropDownListener("#query");
        adjustWidthBySelf("#query");
    });
}

function onClickListener(label, callback) {
    $(label + "-submit").click(function () {
        callback();
    });
}

function pollForQueryResult(callData, delay, itr){
    setTimeout(function () {
        $.ajax({
            type: "POST",
            url: '/operation/',
            data: JSON.stringify(callData),
            statusCode: {
                // Success
                200: function ( data ) {
                    console.log("DATA >> " + data)
                    window.dialog.close();

                    resMessage = callData["function-name"] + "('" + callData["query"] + "') at " + callData["dataset-name"] + " is: " + data
                    BootstrapDialog.show({
                        label: BootstrapDialog.TYPE_SUCCESS,
                        title: function (dialog) {
                            var $title = $('<span class="glyphicon glyphicon-ok-sign" aria-hidden="true"></span> <span>Execution success</span>');
                            return $title;
                        },
                        message: function (dialog) {
                            var $message = $('<strong>Result for ' + callData["function-name"] + ' with argument: "' + callData["query"] + '" is: ' + data + '</strong>');
                            return $message;
                        }
                    });
                },
                // Processing
                202: function () {
                    console.log("Still processing");
                    callData['is-polling'] = true;
                    pollForQueryResult(callData, delay, itr + 1);
                },
                // Invalid data
                400: function () {
                    console.log("Invalid data");
                },
                // Not found
                404: function () {
                    console.log("Not Found");
                },
            }
        });
    }, delay * itr);
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
        - 35);
}
