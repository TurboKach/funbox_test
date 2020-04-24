from django.urls import path
from .views import visited_links, visited_domains

urlpatterns = {
    path('visited_links', visited_links, name="post_links"),
    path('visited_domains', visited_domains, name="get_domains"),
}
