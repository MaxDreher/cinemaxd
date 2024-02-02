$(document).ready(function() {
    // Submit form with AJAX
    $('#customPosterUploadForm').submit(function(e) {
        e.preventDefault(); // Prevent the form from submitting traditionally

        // Get the poster link from the input field
        var posterLink = $('#posterLink').val();
        var movieId = $('[name="movieId"]').val();

        console.log(posterLink)
        // Make an AJAX request to your server to save the link
        $.ajax({
            type: 'POST', // or 'PUT', 'GET', etc.
            url: '/save_poster_link/', // Replace with your actual server endpoint
            data: {
                movieId: movieId,
                posterLink: posterLink
            },
            success: function(response) {
                $('#customPosterUploadForm')[0].reset();
                console.log('Link saved successfully:', response);
                // You can handle the response as needed
            },
            error: function(error) {
                console.error('Error saving link:', error);
                // Handle the error
            }
        });
        location.reload();
    });
});
