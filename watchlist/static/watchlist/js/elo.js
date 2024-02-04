// Function to process Elo Matchup
$(document).ready(function() {
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
                },
            });
    });
});
