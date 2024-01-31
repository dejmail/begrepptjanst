window.onload = function() {
    django.jQuery(document).ready(function() {
        django.jQuery.get('/get_config_options/', function(data) {
            var configOptionValue = data.option_value;  // Adjust this based on your JSON response structure
            if (configOptionValue === 'some_value') {
                django.jQuery('#id_dictionaries').closest('.form-row').hide();
            } else {
                django.jQuery('#id_dictionaries').closest('.form-row').show();
            }
        });

        // If using a custom form, you may need to handle form-specific events
        django.jQuery('#id_config_option').change(function() {
            // Handle change event for the config option field, if necessary
        });
    });
}