from term_list.models import ConfigurationOptions

def global_status_config(request):
    config = ConfigurationOptions.objects.get(name="status-and-colour")  # or filter by name, etc.
    return {
        'status_config': config.config if config else {}
    }