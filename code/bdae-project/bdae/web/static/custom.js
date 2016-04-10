/*
 * Created by Steffen Karlsson on 02-20-2016
 * Copyright (c) 2016 The Niels Bohr Institute at University of Copenhagen. All rights reserved.
 */

$(document).ready(function() {
    var ndDropdown = $("#new-dataset-dropdown");
    var width = ndDropdown.outerWidth(true);
    ndDropdown.outerWidth(0);

    addDropDownListener("#add-registry-name", function ( text ) {
        console.log(">> " + text);
    });

    onClickListener("#update-dataset", function () {
        console.log($("#update-dataset").val());
    });

    $.getJSON( "/get_registered_datasets", function( data ) {
        $.each( data, function( index, name ) {
            $("#dataset-dropdown-menu").append("<li id=\"dataset-first\"><a href=\"#\">" + name + " </a></li>");

//            var element1 = "<li value=\"" + val + "\" id=\"";
//            var element2 = "-dataset-first\"><a href=\"#\">" + val.substring(val.lastIndexOf(".") + 1) + " </a></li>";
//            $("#new-dataset-dropdown-menu").append(element1 + "new" + element2);
        });

        // Adding current dataset supported operations to query
        setDatasetFunctions($("#dataset-first").text());
        addDropDownListener("#dataset", function( text ) {
            setDatasetFunctions(text);
        });

        onClickListener("#new-dataset", function () {
            console.log()
        });

        adjustWidth("#remove-dataset", "#new-dataset");
        adjustWidth("#remove-registry-name", "#new-dataset");
        adjustWidth("#update-dataset", "#new-dataset");
        ndDropdown.outerWidth(width).css("display", "inline");

        // Dropdown listener also sets initial value in the menu field
        addDropDownListener("#new-dataset", function( text ) {
            console.log(">> " + text);
        });
        adjustWidthBySelf("#new-dataset", offset=40);

        onClickListener("#query", function () {
            callData = { "dataset-name": window.dataset,
                         "function-name": $.trim($("#query-dropdown-button").text()),
                         "query": $("#query").val(),
                         "is-polling": false };

            showWaitingDialog("Querying");
            pollForQueryResult(callData, 200, 0);
        });
    });
});

function showWaitingDialog (title) {
    window.dialog = BootstrapDialog.show( {
        closable: false,
        message: function (dialog) {
            var $progress = $('<div class="progress"><div class="progress-bar progress-bar-striped active" role="progressbar" aria-valuenow="100" aria-valuemin="0" aria-valuemax="100" style="width: 100%"></div></div>');
            return $progress;
        },
        title: title
    });
}

function showDialog (text_title, text_message, glyph) {
    BootstrapDialog.show({
        label: BootstrapDialog.TYPE_SUCCESS,
        title: function (dialog) {
            var $title = $('<span class="glyphicon ' + glyph +'" aria-hidden="true"></span><span>' + text_title + '</span>');
            return $title;
        },
        message: function (dialog) {
            var $message = $('<strong>' + text_message + '</strong>');
            return $message;
        }
    });
}

function showErrorDialog (text_message) {
    showDialog('Error', text_message, 'glyphicon-remove-circle');
}

function setDatasetFunctions(dataset_name) {
    window.dataset = dataset_name
    $.getJSON("/get_operations/" + dataset_name, function( data ) {
        $.each( data, function( idx, entry ) {
            $("#query-dropdown-menu").empty();
            $("#query-dropdown-menu").append("<li id=\"query-first\"><a href=\"#\">" + entry + " </a></li>");
        });

        addDropDownListener("#query");
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
            url: '/job',
            data: JSON.stringify(callData),
            statusCode: {
                // Success
                200: function ( data ) {
                    console.log("DATA >> " + data);
                    window.dialog.close();

                    message = 'Result for ' + callData["function-name"] + ' with argument: "' + callData["query"] + '" is: ' + data;
                    showDialog('Execution success', message, 'glyphicon-ok-circle');
                },
                // Processing
                202: function () {
                    console.log("Still processing");
                    callData['is-polling'] = true;

                    window.dialog.close();
                    pollForQueryResult(callData, delay, itr + 1);
                },
                // Invalid data
                400: function () {
                    console.log("Invalid data");
                    window.dialog.close();
                    showErrorDialog('Invalid data: Please verify data on the dataset');
                },
                // No data in dataset
                410: function () {
                    console.log("No data in dataset");
                    window.dialog.close();
                    showErrorDialog('The dataset doesn\'t contain any data');
                },
                // Not found
                404: function () {
                    console.log("Not found");
                    window.dialog.close();
                    showErrorDialog('Dataset doesn\'t exists');
                },
            }
        });
    }, delay * itr);
}

function addDropDownListener(label, valueCallback) {
    $(label + "-dropdown-selection").text($(label + "-first").text())
    $(label + "-dropdown-menu li a").click(function(){
        var selText = $(this).text();
        console.log($(this));
        $(label + "-dropdown-selection").text(selText + " ");
        adjustWidthBySelf(label);

        if (valueCallback !== null)
            valueCallback(selText);
    });

    adjustWidthBySelf(label);
}

function adjustWidthBySelf(label, offset = 35) {
    adjustWidth(label, label, offset)
}

function adjustWidth(toLabel, fromLabel, offset = 35) {
    $(toLabel).width($(".page-header").width()
        - $(fromLabel + "-submit").outerWidth(true)
        - $(fromLabel + "-dropdown").outerWidth(true)
        - ($(fromLabel).outerWidth(true) - $(fromLabel).innerWidth())
        - offset);
}
