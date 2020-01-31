from django.contrib import admin

# Register your models here.
from ordbok.models import Begrepp, Bestallare, Doman

admin.site.register(Begrepp)
admin.site.register(Beställare)
admin.site.register(Domän)