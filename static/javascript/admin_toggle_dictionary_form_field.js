window.onload = function() {
    const endpoint = endpoint_check();
    const url = endpoint + 'get_config_options/?option=dictionaries_inline';
    console.log('Getting ' + url);
    django.jQuery(document).ready(function() {
        django.jQuery.get(url, function(data) {
            var configOptionValue = data.is_active;  // Adjust this based on your JSON response structure
            debugger;
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