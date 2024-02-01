window.onload = function() {
    var currentUrl = window.location.href;
    var baseUrl = currentUrl.split('/').slice(0,4).join('/')+'/';
    var url = baseUrl + 'get_config_options/?option=dictionaries_inline';
    console.log('Getting config from ' + url);
    django.jQuery(document).ready(function() {
        django.jQuery.get(url, function(data) {
            var configOptionValue = data.is_active;
            if (configOptionValue === false) {
                django.jQuery('div.field-dictionaries').closest('.form-row').hide();
            } else {
                django.jQuery('div.field-dictionaries').closest('.form-row').show();
            }
        });

        // If using a custom form, you may need to handle form-specific events
        django.jQuery('#id_config_option').change(function() {
            // Handle change event for the config option field, if necessary
        });
    });
}