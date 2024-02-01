window.onload = function() {
    django.jQuery(document).ready(function($) {
        $('.image-thumbnail').click(function() {
            var imageUrl = $(this).attr('src');
            var modalHtml = '<div class="modal-overlay"></div>' + '<div class="image-modal"><img src="' + imageUrl + '"></div>';
            $(modalHtml).appendTo('body').fadeIn();

            // Center the modal
            var modal = $('.image-modal');
            var windowHeight = $(window).height();
            var windowWidth = $(window).width();
            var modalHeight = modal.outerHeight();
            var modalWidth = modal.outerWidth();
            var scrollTop = $(window).scrollTop();
            modal.css({
                'top': scrollTop + (windowHeight - modalHeight) / 2 + 'px',
                'left': '50%',
                'transform': 'translateX(-50%)',
                'position': 'absolute',
                'z-index': '9999'
            });

            // Calculate maximum dimensions for the image
            var maxWidth = windowWidth * 0.8; // 80% of window width
            var maxHeight = windowHeight * 0.8; // 80% of window height
            var img = $('.image-modal img');
            var imgWidth = img.width();
            var imgHeight = img.height();
            var aspectRatio = imgWidth / imgHeight;
            if (imgWidth > maxWidth || imgHeight > maxHeight) {
                if (imgWidth / aspectRatio > maxWidth) {
                    img.css('width', maxWidth + 'px');
                    img.css('height', (maxWidth / aspectRatio) + 'px');
                } else {
                    img.css('height', maxHeight + 'px');
                    img.css('width', (maxHeight * aspectRatio) + 'px');
                }
            }

            // Darken the overlay
            $('.modal-overlay').css({
                'position': 'fixed',
                'top': '0',
                'left': '0',
                'width': '100%',
                'height': '100%',
                'background-color': 'rgba(0, 0, 0, 0.5)', // Semi-transparent black
                'z-index': '9998' // Behind the modal
            });
        });

        $(document).on('click', '.image-modal, .modal-overlay', function() {
            $('.image-modal, .modal-overlay').fadeOut(function() {
                $(this).remove();
            });
        });
    });
};
