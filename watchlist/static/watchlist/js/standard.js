$(document).ready(function() {
    $(window).on("scroll", function(e) {
        var navbar = $('#navbar');
        if (window.scrollY > 0) {
            navbar.addClass('tiny');
            navbar.find('.nav-link svg').addClass('tiny-svg');
        } else {
            navbar.removeClass('tiny');
            navbar.find('.nav-link svg').removeClass('tiny-svg');
        }
    });
});

$(document).ready(function() {
    $(document).on('click', '.movie-title', function(e) {
        var movieId = $(this).data('movie-id');
        
        $.ajax({
            url: '/sidebar_ajax/' + movieId + '/',
            method: 'GET',
            success: function(response) {
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
