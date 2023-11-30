/* Copyright 2020 by Chunrong Huang, Solis-Lemus Lab, WID.
  All rights reserved.
  This file is part of the BioKlustering Website. */

// make sure the filelist container size is proportional to the file upload container size
function resize() {
    let height = $('.upload_container').height();
    let width = $('.upload_container').width();
    $('.filelist_container').height(height);
    $('.filelist_container').width(width);
    if(screen.width > 760) {
        $('.filelist_container').width(1.5*width);
    }
}

$(window).on('load', function() {
    $("#submit_params_btn").attr("disabled",false);
    $("#inputfile_sequence").attr("accept", ".fa, .fasta");
    $("#inputfile_label").attr("accept", ".csv");
    // resize();
    // alert message for empty filelist when making a prediction
    $("#submit_params_btn").click(function() {
        if(filelist.length === 0 || filelistError.length) {
            $("#submit_params_alert1").click();
            return false;
        }

        let model = $('#id_mlmodels').find(":selected").text();
        if(model[0] == "S") {
            let filelist2 = $('#id_filelist_form-filelist .table_row input[type=checkbox]').filter(function() {
                return this.checked;
            });
            for(let i = 0; i < filelist2.length; i++) {
                let id = filelist2[i].id;
                let numFiles = document.getElementById(id).labels;
                // for semi-supervised, give warnings if the label file is not submited
                if(numFiles.length == 2 && numFiles[1].innerHTML == "None") {  
                    $("#submit_params_alert2").click();
                    return false;
                }
            }
        }
    })
    // save parameter values once user finished typing
    $(".param").keyup(function() {
        sessionStorage.setItem('scrollpos', window.scrollY);
        $("#update_params_btn").click();
    })
    // enable the parameter tooltip js
    $(function () {
        $('[data-toggle="tooltip"]').tooltip({
            html: true
        })
    })

    // preserve the current position on refresh or submit
    $("#choose_model_form select").on('change', function() {
        $("#submit_params_btn").attr("disabled",true);
        $("#choose_model_form").submit();
        sessionStorage.setItem('scrollpos', window.scrollY);
    })
    $("#choose_model_btn").click(function() {
        sessionStorage.setItem('scrollpos', window.scrollY);
    })
    $("#add_to_pred_btn").click(function() {
        sessionStorage.setItem('scrollpos', window.scrollY);
    })
    $("#del_files_btn").click(function() {
        sessionStorage.setItem('scrollpos', window.scrollY);
    })
    $("#file_upload_btn").click(function() {
        sessionStorage.setItem('scrollpos', window.scrollY);
    })

    // make sure the select all checkbox functions well
    $("#select_all").click(function() {
        sessionStorage.setItem('selectAll', this.checked);
        $("tbody input[type=checkbox]").prop("checked", this.checked);
        $("#add_to_pred_btn").click();
    })
    // save the file list when any checkbox is checked
    $('tbody input[type=checkbox]').on('change', function() { 
        $("#add_to_pred_btn").click();
    });
})

// $(window).resize(function() {
//     resize();
// })

// preserve some data on refresh or submit
document.addEventListener("DOMContentLoaded", function (event) {
    // preserve the current position on refresh or submit
    let scrollpos = sessionStorage.getItem('scrollpos');
    if (scrollpos) {
        window.scrollTo(0, scrollpos);
        sessionStorage.removeItem('scrollpos');
    }
    // make sure the select all checkbox functions well
    let unchecked = $("tbody input[type=checkbox]").filter(function() {
        return !this.checked;
    })
    if(unchecked.length != 0) {
        $("#select_all").prop('checked', false);
    } else {
        $("#select_all").prop('checked', true);
    }
});
