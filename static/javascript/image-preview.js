window.onload = function() {
    django.jQuery(document).ready(function($) {
        $('.image-thumbnail').click(function() {
            var imageUrl = $(this).attr('src');
            var modalHtml = '<div class="image-modal"><img src="' + imageUrl + '"></div>';
            $(modalHtml).appendTo('body').fadeIn();
        });

        $(document).on('click', '.image-modal', function() {
            $(this).fadeOut(function() {
                $(this).remove();
            });
        });
    });
};