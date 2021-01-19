from django.conf import settings
from django.conf.urls import handler404, handler500
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path('auth/', include('users.urls')),
    path('auth/', include('django.contrib.auth.urls')),
    path('admin/', admin.site.urls),
    path('about/', include('about.urls', namespace='about')),
    path('', include('posts.urls', namespace='posts')),
]

handler404 = 'posts.views.page_not_found' # noqa

handler500 = 'posts.views.server_error' # noqa

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    import debug_toolbar
    urlpatterns += (path('__debug__/', include(debug_toolbar.urls)),)

urlpatterns += staticfiles_urlpatterns()

urlpatterns += [re_path(
    r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT})]
