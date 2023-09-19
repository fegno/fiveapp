from django.shortcuts import render
from django.db.models import Q,Sum,Prefetch,F,Exists, OuterRef
from django.utils import timezone
from django.db import transaction
from django.http import HttpResponse

from rest_framework.response import Response
from superadmin.models import ModuleDetails, BundleDetails
from rest_framework.permissions import AllowAny, IsAuthenticated
from user.api_permissions import CustomTokenAuthentication, IsAdmin
from rest_framework.views import APIView
from rest_framework import status
from datetime import timedelta, date, datetime

from superadmin.models import ModuleDetails, FeatureDetails,  BundleDetails
from payment.models import PaymentAttempt
from administrator.models import PurchaseDetails

import json
import stripe
import requests
from fiveapp import settings


class InitiatePayment(APIView):
	permission_classes=(IsAuthenticated,IsCustomer)

	def post(self,request):
		response_dict={'status':False}
        bundle_ids = request.data.getlist("bundle_ids")
        modules_ids = request.data.getlist("modules_ids")
        total_price = request.data.get("total_price")
        modules_ids = request.data.getlist("modules_ids")
        subscription_type = request.data.get("subscription_type")

        order = PurchaseDetails.objects.create(
            user=request.user,
            status="Pending",
            subscription_type=subscription_type,
            total_price=total_price
        )
        order.module.add(*request.POST.getlist("modules_ids"))      
        order.bundle.add(*request.POST.getlist("bundle_ids"))    
        if subscription_type == "WEEK":
            order.subscription_start_date =  timezone.now().date()
            end_date = timezone.now().date()  + timedelta(days=7)
            order.subscription_end_date =  end_date
        elif  subscription_type == "MONTH":
            order.subscription_start_date =  timezone.now().date()
            end_date = timezone.now().date()  + timedelta(days=30)
            order.subscription_end_date =  end_date
        elif subscription_type == "YEAR":
            order.subscription_start_date =  timezone.now().date()   
            end_date = timezone.now().date()  + timedelta(days=365)
            order.subscription_end_date =  end_date
        order.save()
		with transaction.atomic():
			stripe.api_key=settings.STRIPE_API_KEY
			intent = stripe.PaymentIntent.create(amount=round(order.total_price*100),currency='aed')
			payment_attempt=PaymentAttempt.objects.create(parchase=order,user=request.user,currency='aed',amount=order.total_price,
				status='Initiated',client_secret=intent['client_secret'],payment_intent_id=intent['id'],last_attempt_date=timezone.now())
		
			response_dict['client_secret']=payment_attempt.client_secret
			response_dict['status']=True
		return Response(response_dict,HTTP_200_OK)


class StripePaymentWebhook(APIView):
	permission_classes=(AllowAny,)

	def post(self,request):
		stripe.api_key=settings.STRIPE_API_KEY
		try:
			event = stripe.Event.construct_from(request.data,stripe.api_key)
		except ValueError as e:
			return HttpResponse(status=400)
		if event.type == 'payment_intent.succeeded':
			intent = event.data.object # contains a stripe.PaymentIntent
			payment_attempt=PaymentAttempt.objects.filter(payment_intent_id=intent['id'],is_active=True).first()
			if not payment_attempt:
				return HttpResponse(status=404)
			payment_attempt.status='succeeded'
			payment_attempt.charges_json=json.dumps(intent['charges'])
			payment_attempt.total_charge=sum(i['amount'] for i in intent['charges']['data'])
			order=payment_attempt.parchase
			payment_attempt.save()
			order.status='Placed'
			order.received_amount=intent['amount_received']/100
			order.payment_date=timezone.now()
			order.save()
		elif event.type == 'payment_intent.cancelled':
			intent = event.data.object # contains a stripe.PaymentIntent
			payment_attempt=PaymentAttempt.objects.filter(payment_intent_id=intent['id'],is_active=True).first()
			if not payment_attempt:
				return HttpResponse(status=404)
			with transaction.atomic():
				payment_attempt.status='Cancelled'
				payment_attempt.save()
				
		return HttpResponse(status=200)
