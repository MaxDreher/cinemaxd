function generateData(count, yrange) {
    var i = 0;
    var series = [];
    while (i < count) {
      var x = (i + 1).toString();
      var y =
      Math.floor(Math.random() * (yrange.max - yrange.min + 1)) + yrange.min;
    
      series.push({
        x: x,
        y: y
      });
      i++;
    }
    return series;
}

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
  // Submit form with AJAX
  $('#randomButton').click(function(e) {
    console.log("BUTTON PRESSED");
      // Show loading spinner
      // $('#submitButton').addClass('disabled');
      // $('#submitText').addClass('d-none');
      // $('#loadingSpinner').removeClass('d-none');

      // Make AJAX request
      $.ajax({
          url: '/get_random_movies/',  // Replace with your Django endpoint
          type: 'GET',
          data: $(this).serialize(),
          success: function(response) {
            console.log(response)
              $('#randomSelections').html(response);
          },
          error: function(error) {
              console.error('Error:', error);
              // Handle error if necessary
          },
          complete: function() {
              // Hide loading spinner when request is complete
              // $('#loadingSpinner').addClass('d-none');
              // $('#submitButton').removeClass('disabled');
              // $('#submitText').removeClass('d-none');        
          }
      });
  });
});

    