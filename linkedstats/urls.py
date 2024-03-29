from django.conf.urls.defaults import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^/?$', 'website.views.index'),
    url(r'^doc/?$', 'website.views.doc'),
    url(r'^population/?$', 'website.views.population'),
    url(r'^municipality/?$', 'website.views.municipality_search'),
    url(r'^municipality/(?P<municipality_name>[\w\ -]+)/?$', 'website.views.municipality'),
)

urlpatterns += staticfiles_urlpatterns()
