from django.conf.urls import include
from administrator import api
from django.urls import path, re_path

urlpatterns = [
    re_path(r'^home-page/', api.Homepage.as_view(), name='home-page'),
    re_path(r'^list-subscription-plans/', api.ListSubscriptionPlans.as_view(), name='list-subscription-plans'),
    re_path(r'^view-bundle-details/(?P<pk>\d+)/$', api.ViewBundle.as_view()),
    re_path(r'^select-free-subscription/', api.SelectFreeSubscription.as_view(), name='select-free-subscription'),

    re_path(r'^list-bundle-modules/(?P<pk>\d+)/', api.ListBundleModules.as_view(), name='list-bundle-modules'),
    re_path(r'^list-modules/', api.ListModules.as_view(), name='list-modules'),
    
    re_path(r'^module-users/(?P<pk>\d+)/$', api.UserInModule.as_view(), name='users-under-the-module'),
    re_path(r'^user-delete/(?P<module_id>\d+)/(?P<pk>\d+)/$', api.DeleteUserFromModule.as_view(), name='delete-user'),
    re_path(r'^user-un-assign/(?P<pk>\d+)/$', api.UnAssignUserlist.as_view(), name='user-unassign'),
    re_path(r'^user-assign/(?P<pk>\d+)/$', api.AssignUser.as_view(), name='user-assign'),

    re_path(r'^admin-modules/', api.AdminModules.as_view(), name='admin-modules'),
    re_path(r'^user-invite/', api.UserInviteModule.as_view(), name='users-invite-to-module'),

    re_path(r'^user-module-list/(?P<pk>\d+)/$', api.UserModuleList.as_view(), name='user-module-list'),
    re_path(r'^remove-module/(?P<user_id>\d+)/(?P<module_id>\d+)/$', api.DeleteModule.as_view(), name='remove-module'),
    re_path(r'^unassign-module/(?P<pk>\d+)/$', api.UnassignedModule.as_view(), name= 'unassigned-module'),
    re_path(r'^modules-assign/(?P<pk>\d+)/$', api.AssignModulesToUser.as_view(), name='modules-assign'),

    re_path(r'^permanent-delete-user/(?P<pk>\d+)/$', api.PermanentDeleteUserFromAdmin.as_view(), name='permanent-delete-user'),

    re_path(r'^upload-csv/(?P<pk>\d+)/$', api.UploadCsv.as_view(), name='upload-csv'),
    re_path(r'^list-csv/(?P<pk>\d+)/$', api.ListCsv.as_view(), name='list-csv'),
    re_path(r'^view-csv/(?P<pk>\d+)/$', api.ViewCsv.as_view(), name='view-csv'),
    re_path(r'^generate-report/(?P<pk>\d+)/$', api.GenerateReport.as_view(), name='generate-report'),
    re_path(r'^view-report/(?P<pk>\d+)/$', api.ViewReport.as_view(), name='view-report'),
    re_path(r'^analytics-report/(?P<pk>\d+)/$', api.AnalyticsReport.as_view(), name='analytics-report'),

]