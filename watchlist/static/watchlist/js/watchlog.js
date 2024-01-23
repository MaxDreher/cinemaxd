$(document).ready(function() {
    // Initialize variables for debouncing
    let debounceTimer;

    // Attach an event listener to the input fields
    $('#id_title, #id_year').on('input', function() {
        // Clear previous debounce timer
        clearTimeout(debounceTimer);

        // Set a new debounce timer
        debounceTimer = setTimeout(function() {
            // Call the fetchMovieInfo function after the debounce time
            fetchMovieInfo();
        }, 500);
    });

    function fetchMovieInfo() {
        // Check if both fields are filled
        const movieName = $('#id_title').val();
        const releaseYear = $('#id_year').val();

        if (movieName && releaseYear) {
            // Make AJAX request
            $.ajax({
                url: '/get_movie_info/',
                type: 'GET',
                data: {
                    'id_title': movieName,
                    'id_year': releaseYear,
                },
                success: function(response) {
                    // Display the actual movie poster
                    const posterUrl = response.poster_url;
                    $('#moviePosterContainer').html(`<img src="${posterUrl}" class="img-fluid rounded" alt="Movie Poster">`);
                },
                error: function(error) {
                    console.error('Error fetching movie info:', error);
                    // If there's an error, you may want to show an error message or keep the placeholder
                },
            });
        } else {
            // If either field is empty, clear the poster and show the placeholder
            $('#moviePosterContainer').html('<i class="bi bi-film" style="font-size: 2em; color: #6c757d;"></i>');
        }
    }
});

$(document).ready(function() {
    // Submit form with AJAX
    $('#watchlogInput').submit(function(e) {
        e.preventDefault(); // Prevent the form from submitting traditionally

        // Show loading spinner
        $('#submitButton').addClass('disabled');
        $('#submitText').addClass('d-none');
        $('#loadingSpinner').removeClass('d-none');

        // Make AJAX request
        $.ajax({
            url: '/watchlist/watchlog/',  // Replace with your Django endpoint
            type: 'POST',
            data: $(this).serialize(),
            success: function(response) {
                $('#searchPanes').html('');
                $('#sidebar-header').html('');
                $('#tableContainer').html('');
                $('#tableContainer').html(response.table_html);
                console.log(response.title_year)
                $('#successAlert').html(response.title_year);
                $('#successAlert').removeClass('d-none');
            },
            error: function(error) {
                console.error('Error:', error);
                // Handle error if necessary
            },
            complete: function() {
                // Hide loading spinner when request is complete
                $('#loadingSpinner').addClass('d-none');
                $('#submitButton').removeClass('disabled');
                $('#submitText').removeClass('d-none');        
            }
        });
    });
});

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

var collapseButton = document.getElementById('collapseButton');
var collapseIcon = document.getElementById('collapseIcon');

collapseButton.addEventListener('click', function () {
  // Toggle icon based on collapse state
  if (collapseButton.getAttribute('aria-expanded') === 'true') {
    collapseIcon.classList.remove('bi-plus-circle');
    collapseIcon.classList.add('bi-dash-circle');
  } else {
    collapseIcon.classList.remove('bi-dash-circle');
    collapseIcon.classList.add('bi-plus-circle');
  }
});
