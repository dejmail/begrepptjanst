
from django.urls import include, path
from . import views
from begrepptjanst.routers import router

urlpatterns = [
    path('', views.index, name='index'),
    #path('api/', include(router.urls))
]
