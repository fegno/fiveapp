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
from administrator.models import PurchaseDetails, SubscriptionDetails

import json
import stripe
import requests
from fiveapp import settings


class InitiatePayment(APIView):
	permission_classes = (IsAuthenticated,)
	authentication_classes = (CustomTokenAuthentication,)

	def post(self,request):
		response_dict={'status':False}
		bundle_ids = request.data.get("bundle_ids")
		modules_ids = request.data.get("modules_ids")
		total_price = request.data.get("total_price")
		subscription_type = request.data.get("subscription_type")

		order = PurchaseDetails.objects.create(
			user=request.user,
			status="Pending",
			subscription_type=subscription_type,
			total_price=total_price,
			is_subscribed=False
		)
		order.module.add(*request.POST.getlist("modules_ids"))      
		order.bundle.add(*request.POST.getlist("bundle_ids"))    
		subscription = SubscriptionDetails.objects.filter(
			user=order.user, 
			is_subscribed=True
		).last()
		if subscription_type == "WEEK":
			order.subscription_start_date =  timezone.now().date()
			if subscription:
				end_date = subscription.subscription_end_date
			else:
				end_date = timezone.now().date()  + timedelta(days=7)
			order.subscription_end_date =  end_date
		elif  subscription_type == "MONTH":
			order.subscription_start_date =  timezone.now().date()
			if subscription:
				end_date = subscription.subscription_end_date
			else:
				end_date = timezone.now().date()  + timedelta(days=30)
			order.subscription_end_date =  end_date
		elif subscription_type == "YEAR":
			order.subscription_start_date =  timezone.now().date() 
			if subscription:
				end_date = subscription.subscription_end_date
			else:  
				end_date = timezone.now().date()  + timedelta(days=365)
			order.subscription_end_date =  end_date
		order.save()
		with transaction.atomic():
			stripe.api_key=settings.STRIPE_API_KEY
			intent = stripe.PaymentIntent.create(amount=round(order.total_price*100),currency='gbp')
			payment_attempt=PaymentAttempt.objects.create(parchase_user_type="Subscription",parchase=order,user=request.user,currency='gbp',amount=order.total_price,
				status='Initiated',client_secret=intent['client_secret'],payment_intent_id=intent['id'],last_attempt_date=timezone.now())
		
			response_dict['client_secret']=payment_attempt.client_secret
			response_dict['status']=True
		return Response(response_dict,status.HTTP_200_OK)


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

			if payment_attempt.status != "Placed":
				PaymentAttempt.objects.filter(payment_intent_id=intent['id']).update(
					last_payment_json=json.dumps(event)
				)
				payment_attempt.status='succeeded'
				payment_attempt.charges_json=json.dumps(intent['charges'])
				payment_attempt.total_charge=sum(i['amount'] for i in intent['charges']['data'])
				order=payment_attempt.parchase
				payment_attempt.save()
				order.status='Placed'
				order.received_amounts=intent['amount_received']/100
				order.payment_dates=timezone.now()
				order.save()
				user = order.user
				user.is_subscribed = True
				user.save()
				if SubscriptionDetails.objects.filter(user=order.user):
					subscription = SubscriptionDetails.objects.filter(user=order.user).last()
					if subscription.subscription_end_date < timezone.now().date():
						subscription.module.clear()
						subscription.bundle.clear()
						subscription.module.add(order.module.values_list("id", flat=True))      
						subscription.bundle.add(order.bundle.values_list("id", flat=True))    
						subscription.save()
					else:
						subscription.module.add(order.module.values_list("id", flat=True))      
						subscription.bundle.add(order.bundle.values_list("id", flat=True))    
						subscription.save()
				else:
					subscription = SubscriptionDetails.objects.create(
						user=order.user,
						subscription_start_date=order.subscription_start_date,
						subscription_end_date=order.subscription_end_date,
						is_subscribed=True,
						subscription_type=order.subscription_type,
					)
					subscription.module.add(order.module.values_list("id", flat=True))      
					subscription.bundle.add(order.bundle.values_list("id", flat=True))    
					subscription.save()
		elif event.type == 'payment_intent.cancelled':
			intent = event.data.object # contains a stripe.PaymentIntent
			payment_attempt=PaymentAttempt.objects.filter(payment_intent_id=intent['id'],is_active=True).first()
			if not payment_attempt:
				return HttpResponse(status=404)
			PaymentAttempt.objects.filter(payment_intent_id=intent['id']).update(
				last_payment_json=json.dumps(event)
			)
			with transaction.atomic():
				payment_attempt.status='Cancelled'
				payment_attempt.save()
				
		return HttpResponse(status.HTTP_200_OK)

class InitiateUserPayment(APIView):
	permission_classes = (IsAuthenticated,)
	authentication_classes = (CustomTokenAuthentication,)

	def post(self,request):
		response_dict={'status':False}
		user_count = request.data.get("user_count")
		total_price = request.data.get("total_price")
		subscription_type = request.data.get("subscription_type")

		subscription = SubscriptionDetails.objects.filter(
			user=order.user, 
			is_subscribed=True
		).last()
		if not subscription:
			response_dict['error']= "No active subscription"
			return Response(response_dict,status.HTTP_200_OK)

		order = PurchaseDetails.objects.create(
			user=request.user,
			status="Pending",
			subscription_type=subscription_type,
			total_price=total_price,
			is_subscribed=False,
			subscription_end_date=subscription.subscription_end_date,
			subscription_start_date=order.subscription_start_date,
			user_count=user_count,
			parchase_user_type="User"
		)
		with transaction.atomic():
			stripe.api_key=settings.STRIPE_API_KEY
			intent = stripe.PaymentIntent.create(amount=round(order.total_price*100),currency='gbp')
			payment_attempt=PaymentAttempt.objects.create(parchase_user_type="User",parchase=order,user=request.user,currency='gbp',amount=order.total_price,
				status='Initiated',client_secret=intent['client_secret'],payment_intent_id=intent['id'],last_attempt_date=timezone.now())
		
			response_dict['client_secret']=payment_attempt.client_secret
			response_dict['status']=True
		return Response(response_dict,status.HTTP_200_OK)