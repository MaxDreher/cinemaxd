$(document).ready(function() {
    $(document).on('click', '.movie-title', function(e) {
        var movieId = $(this).data('movie-id');
        
        $.ajax({
            url: '/sidebar_ajax/' + movieId + '/',
            method: 'GET',
            success: function(response) {
                $('#sidebarContainer').html(response);
                var newId = movieId + '-offcanvas'
                var myOffcanvas = new bootstrap.Offcanvas(document.getElementById(newId));
                myOffcanvas.toggle();
                var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
                var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
                });
            },
            error: function(error) {
                console.error('Error fetching sidebar content:', error);
            }
        });
    });
});

$(document).ready(function() {
    $(document).on('click', '.actor-name', function(e) {
        var actorId = $(this).data('actor-id');
        
        $.ajax({
            url: '/sidebar_actor_ajax/' + actorId + '/',
            method: 'GET',
            success: function(response) {
                $('#sidebarContainer').html(response);
                var newId = actorId + '-person-offcanvas'
                var myOffcanvas = new bootstrap.Offcanvas(document.getElementById(newId));
                myOffcanvas.toggle();
                var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
                var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
                });
            },
            error: function(error) {
                console.error('Error fetching sidebar content:', error);
            }
        });
    });
});

