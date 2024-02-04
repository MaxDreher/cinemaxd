// Function to refresh Random Movies
$(document).ready(function() {
  $('#randomButton').click(function(e) {
      $.ajax({
          url: '/get_random_movies/',
          type: 'GET',
          data: $(this).serialize(),
          success: function(response) {
              $('#randomElements').html(response);
          },
          error: function(error) {
              console.error('Error:', error);
          },
          complete: function() {
          }
      });
  });
});

    