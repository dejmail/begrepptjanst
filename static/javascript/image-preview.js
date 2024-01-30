
    django.jQuery(document).ready(function() {
        django.jQuery('.image-thumbnail').click(function() {
            var imageUrl = django.jQuery(this).attr('src');
            var modalHtml = '<div class="image-modal"><img src="' + imageUrl + '"></div>';
            django.jQuery(modalHtml).appendTo('body').fadeIn();
        });

        django.jQuery(document).on('click', '.image-modal', function() {
            django.jQuery(this).fadeOut(function() {
                django.jQuery(this).remove();
            });
        });
    });
