// Function to refresh Random Movies
$(document).ready(function() {
  $('#random-button').click(function(e) {
      $.ajax({
          url: '/get_random_movies/',
          type: 'GET',
          data: $(this).serialize(),
          success: function(response) {
              $('#random-elements').html(response);
          },
          error: function(error) {
              console.error('Error:', error);
          },
          complete: function() {
            var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
              return new bootstrap.Tooltip(tooltipTriggerEl);
            });
          }
      });
  });
});

var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
  return new bootstrap.Tooltip(tooltipTriggerEl);
});
