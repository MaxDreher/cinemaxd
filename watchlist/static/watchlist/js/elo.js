// Function to process Elo Matchup
$(document).ready(function() {
    $(document).on('click', '.z-2.btn.btn-secondary.roboto.mt-3', function() {
        var winnerId = $(this).attr('id');
        var loserId = $('.z-2.btn.btn-secondary.roboto.mt-3').not(this).attr('id');
        handleEloMatchup(winnerId, loserId)
    })
});

$(document).keydown(function(e) {
    // Check if left arrow key (code 37) or right arrow key (code 39) is pressed
    if (e.keyCode === 37) {
        // Find the active button (the one with focus)
        var winnerId = $('.z-2.btn.btn-secondary.roboto.mt-3:first').attr('id');
        var loserId = $('.z-2.btn.btn-secondary.roboto.mt-3:last').attr('id');
        handleEloMatchup(winnerId, loserId)
    }
    else if (e.keyCode === 39) {
        var loserId = $('.z-2.btn.btn-secondary.roboto.mt-3:first').attr('id');
        var winnerId = $('.z-2.btn.btn-secondary.roboto.mt-3:last').attr('id');
        handleEloMatchup(winnerId, loserId)
    }
});

function handleEloMatchup(winnerId, loserId) {
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
            var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        },
        error: function(error) {
            console.error('Error fetching movie info:', error);
        },
})};

var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
return new bootstrap.Tooltip(tooltipTriggerEl);
});
