$(document).ready(function() {
    // Use event delegation for dynamically added elements
    $(document).on('click', '.movie-title', function(e) {
        // e.preventDefault();
  
        var movieId = $(this).data('movie-id');
        
        $.ajax({
            url: '/sidebar_ajax/' + movieId + '/',
            method: 'GET',
            success: function(response) {
                // Append the response to the sidebar container
                $('#sidebarContainer').html(response);
                var myOffcanvas = new bootstrap.Offcanvas(document.getElementById(movieId));
                myOffcanvas.toggle();
            },
            error: function(error) {
                console.error('Error fetching sidebar content:', error);
            }
        });
    });
});

$(document).ready(function() {
    // Use event delegation for dynamically added elements
    $(document).on('click', '.z-2.btn.btn-secondary.roboto.mt-3', function() {
        var winnerId = $(this).attr('id');
        var loserId = $('.z-2.btn.btn-secondary.roboto.mt-3').not(this).attr('id');

        console.log('Winner ID:', winnerId);
        console.log('Loser ID:', loserId);

        $.ajax({
                url: '/elo_matchup/',
                type: 'GET',
                data: {
                    'id_winner': winnerId,
                    'id_loser': loserId,
                },
                success: function(response) {
                    $('#eloContainer').html(response);
                },
                error: function(error) {
                    console.error('Error fetching movie info:', error);
                    // If there's an error, you may want to show an error message or keep the placeholder
                },
            });
    });
});
