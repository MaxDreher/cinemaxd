$(document).ready(function () {
    // Handle image click event
    $('.image-select').click(function () {
        $('.image-select').removeClass('active-image'); // Remove active class from all images
        $(this).addClass('active-image'); // Add active class to the clicked image
    });

    $('#modalSubmit').click(function () {
        // Get the src of the active image
        $('#modalSubmit').addClass('disabled');
        $('#modalSubmitText').addClass('d-none');
        $('#modalSpinner').removeClass('d-none');

        var movieId = $(this).data('movie-id');
        var activeImageSrc = $('.active-image').attr('src');
        // Send AJAX request to Django
        $.ajax({
            type: 'POST',
            url: '/poster_update/',
            data: { 
                poster: activeImageSrc,
                movie: movieId,
            },
            success: function (response) {
                // Handle success
                console.log('Link saved successfully:', response);
                location.reload();
                $('#modalSpinner').addClass('d-none');
                $('#modalSubmit').removeClass('disabled');
                $('#modalSubmitText').removeClass('d-none');
            },
            error: function (error) {
                // Handle error
                console.error('Error saving image:', error);
            }
        });
    });
})