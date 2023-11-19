from django.conf.urls import include
from payment import api
from django.urls import path, re_path

urlpatterns = [
    re_path(r'^initiate-payment/', api.InitiatePayment.as_view(), name='initiate-payment'),
    re_path(r'^payment-webhook/', api.StripePaymentWebhook.as_view(), name='payment-webhook'),
    re_path(r'^initiate-user-payment/', api.InitiateUserPayment.as_view(), name='initiate-user-payment'),
    re_path(r'^initiate-user-payment-v2/', api.InitiateUserPaymentV2.as_view(), name='initiate-user-payment-v2'),

    re_path(r'^module-bundle-purchase-price/', api.ModuleBundlePurchaserice.as_view(), name='module-bundle-purchase-price'),

    re_path(r'^mock-initiate-payment/', api.MockInitiatePayment.as_view(), name='mock-initiate-payment'),

]