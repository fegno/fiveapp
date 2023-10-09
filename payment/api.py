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
from administrator.models import PurchaseDetails, SubscriptionDetails, AddToCart

import json
import stripe
import requests
from fiveapp import settings


class InitiatePayment(APIView):
	permission_classes = (IsAuthenticated,)
	authentication_classes = (CustomTokenAuthentication,)

	def post(self,request):
		response_dict={'status':False}
		billing_id = request.data.get("billing_id")
		card_id = request.data.get("card_id")
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
		if modules_ids:
			order.module.add(*request.data.get("modules_ids"))    
		if bundle_ids:  
			order.bundle.add(*request.data.get("bundle_ids"))    
		subscription = SubscriptionDetails.objects.filter(
			user=order.user, 
			is_subscribed=True
		).last()
		if subscription:
			total_days = subscription.subscription_end_date - timezone.now().date()
			total_day = total_days.days
			if subscription_type == "WEEK":
				my_price = total_price/7
				total_price = float(my_price) * float(total_day)

			elif subscription_type == "MONTH":
				my_price = total_price/30
				total_price = float(my_price) * float(total_day)
			
			elif subscription_type == "YEAR":
				my_price = total_price/365
				total_price = float(my_price) * float(total_day)

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

			if order.status != "Placed":
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
				
				if order.parchase_user_type !="User":
					user = order.user
					user.is_subscribed = True
					user.save()
					if SubscriptionDetails.objects.filter(user=order.user):
						subscription = SubscriptionDetails.objects.filter(user=order.user).last()
						if subscription.subscription_end_date < timezone.now().date():
							subscription.subscription_start_date = order.subscription_start_date
							subscription.subscription_end_date = order.subscription_end_date
							subscription.is_subscribed = True
							subscription.module.clear()
							subscription.bundle.clear()
							if order.module:
								subscription.module.add(list(order.module.values_list("id", flat=True)))      
							if order.bundle:
								subscription.bundle.add(list(order.bundle.values_list("id", flat=True)))    
							subscription.save()
						else:
							if order.module:
								subscription.module.add(order.module.values_list("id", flat=True))      
							if order.bundle:
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
						if order.module:
							subscription.module.add(list(order.module.values_list("id", flat=True)))      
						if order.bundle:
							subscription.bundle.add(list(order.bundle.values_list("id", flat=True)))     
						subscription.save()
				else:
					user = order.user
					user.total_users = user.total_users + order.user_count
					user.available_paid_users = user.available_paid_users + order.user_count
					user.save()
					AddToCart.objects.filter(added_by=user, is_active=True).update(is_active=False)
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
		billing_id = request.data.get("billing_id")
		card_id = request.data.get("card_id")
		user_count = request.data.get("user_count")
		total_price = request.data.get("total_price")
		subscription_type = request.data.get("subscription_type")

		subscription = SubscriptionDetails.objects.filter(
			user=request.user, 
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
			subscription_start_date=timezone.now().date(),
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
	



class MockInitiatePayment(APIView):
	permission_classes = (IsAuthenticated,)
	authentication_classes = (CustomTokenAuthentication,)

	def post(self,request):
		response_dict={'status':False}
		billing_id = request.data.get("billing_id")
		card_id = request.data.get("card_id")
		bundle_ids = request.data.get("bundle_ids")
		modules_ids = request.data.get("modules_ids")
		total_price = request.data.get("total_price")
		subscription_type = request.data.get("subscription_type")

		order = PurchaseDetails.objects.create(
			user=request.user,
			status="Placed",
			subscription_type=subscription_type,
			total_price=total_price,
			is_subscribed=True
		)
		if modules_ids:
			for module_id in modules_ids:
				order.module.add(module_id)
		if bundle_ids:
			for bundle_id in bundle_ids:
				order.bundle.add(bundle_id)
		# order.module.add(modules_ids)      
		# order.bundle.add(*request.POST.getlist("bundle_ids"))    
		subscription = SubscriptionDetails.objects.filter(
			user=order.user, 
			is_subscribed=True
		).last()

		


		if subscription:
			if subscription.subscription_end_date < timezone.now().date():
				subscription.subscription_start_date = order.subscription_start_date
				subscription.subscription_end_date = order.subscription_end_date
				subscription.is_subscribed = True
				subscription.module.clear()
				subscription.bundle.clear()
				if order.module:
					subscription.module.add(list(order.module.values_list("id", flat=True)))      
				if order.bundle:
					subscription.bundle.add(list(order.bundle.values_list("id", flat=True)))    
				subscription.save()
			else:
				total_days = subscription.subscription_end_date - timezone.now().date()
				total_day = total_days.days
				if subscription_type == "WEEK":
					my_price = total_price/7
					total_price = float(my_price) * float(total_day)

				elif subscription_type == "MONTH":
					my_price = total_price/30
					total_price = float(my_price) * float(total_day)
				
				elif subscription_type == "YEAR":
					my_price = total_price/365
					total_price = float(my_price) * float(total_day)

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

		if subscription:
			if modules_ids:
				for module_id in modules_ids:
					subscription.module.add(module_id)
			if bundle_ids:
				for bundle_id in bundle_ids:
					subscription.bundle.add(bundle_id)
			subscription.subscription_start_date = timezone.now().date()
			subscription.subscription_end_date = end_date
			subscription.save()
		else:
			subscription = SubscriptionDetails.objects.create(
				user=request.user,
				subscription_start_date=timezone.now().date(),
				subscription_end_date=end_date,
				is_subscribed=True,
				subscription_type=subscription_type
			)
			if modules_ids:
				for module_id in modules_ids:
					subscription.module.add(module_id)
			if bundle_ids:
				for bundle_id in bundle_ids:
					subscription.bundle.add(bundle_id)
		with transaction.atomic():
			payment_attempt=PaymentAttempt.objects.create(parchase_user_type="Subscription",parchase=order,user=request.user,currency='gbp',amount=order.total_price,
				status='Initiated',last_attempt_date=timezone.now())
		
			response_dict['purchase-id']=payment_attempt.id
			response_dict['status']=True

		return Response(response_dict,status.HTTP_200_OK)