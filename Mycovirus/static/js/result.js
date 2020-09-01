$(window).load(function() {
    $("#loading").height(screen.height/2);
    $("#loading").show();
    $("#result").hide();
    $.ajax({
        url: '../process/',
        type: 'POST',
        dataType: 'json',
        data: {csrfmiddlewaretoken: window.CSRF_TOKEN},
        success: function(result){
            $("#loading").remove();
            $('#result_label').append(result.label);
            $("#result").show();
            result.image.forEach(i => {
                $('#result_img').append('<img src="' + "../" + i + '" />');
            });
        },
        error: function(xhr){
            alert("error: " + xhr.responseText); //Remove this when all is fine.
        },
    });
})
