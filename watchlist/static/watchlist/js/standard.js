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
