/* Copyright 2020 by Chunrong Huang, Solis-Lemus Lab, WID.
  All rights reserved.
  This file is part of the Mycovirus Website. */
  
$(window).load(function() {
    $("#loading").height(screen.height/2);
    $("#loading").show();
    $("#result").hide();
    $.ajax({
        url: process,
        type: 'POST',
        dataType: 'json',
        data: {csrfmiddlewaretoken: window.CSRF_TOKEN},
        success: function(result){
            $("#loading").remove();
            $('#result_label').append(result.label);
            $("#result").show();
            if(result.image) { // static image
                result.image.forEach(i => {
                    $('#result_img').append('<img src="' + "../" + i + '" />');
                });
            } else { // dynamic plot
                $('#result_img').append(result.plotly_dash)
            }

        },
        error: function(xhr){
            alert("error: " + xhr.responseText); //Remove this when all is fine.
        },
    });
})
