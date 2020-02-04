
from django.urls import include, path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('view2', views.view2, name= "view2"),
    path('view3', views.view3 , name="view3")
]
