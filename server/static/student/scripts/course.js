$(document).ready(function() {
    $('.flip').on('click',function() {
        $('.blob-more').removeClass('flipped');
    });
    $('.blob-action').on('click',function() {
        $('.flip').click();
        $(this).parent().parent().children('.blob-more').addClass('flipped');
    });
});