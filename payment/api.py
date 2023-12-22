from django.shortcuts import render
from django.db.models import Q,Sum,Prefetch,F,Exists, OuterRef
from django.utils import timezone
from django.db import transaction
from django.http import HttpResponse

from rest_framework.response import Response
from superadmin.models import FreeSubscriptionDetails, ModuleDetails, BundleDetails
from rest_framework.permissions import AllowAny, IsAuthenticated
from user.api_permissions import CustomTokenAuthentication, IsAdmin
from rest_framework.views import APIView
from rest_framework import status

from superadmin.models import ModuleDetails, FeatureDetails,  BundleDetails
from payment.models import PaymentAttempt
from administrator.models import PurchaseDetails, SubscriptionDetails, AddToCart, UserSubscriptionDetails
from user.models import CardDetails, BillingDetails, UserProfile

import json
import stripe
import requests
from fiveapp import settings
from datetime import timedelta, date, datetime
from django.views.decorators.csrf import csrf_exempt


class ModuleBundlePurchaserice(APIView):
	permission_classes = (IsAuthenticated,)
	authentication_classes = (CustomTokenAuthentication,)

	def post(self, request):
		response_dict = {"status":True}

		bundle_ids = request.data.get("bundle_ids", [])
		modules_ids = request.data.get("modules_ids", [])

		subscription = SubscriptionDetails.objects.filter(user=request.user, is_active=True).first()
		if subscription is None:
			return Response({"error": "Admin subscription not found"}, status=status.HTTP_404_NOT_FOUND)
		if not hasattr(subscription, 'subscription_end_date'):
			return Response({"error": "Admin subscription doesn't have a subscription_end_date"}, status=status.HTTP_400_BAD_REQUEST)

		current_date = datetime.now().date()
		subscription_end_date = subscription.subscription_end_date
		remaining_days = (subscription_end_date - current_date).days

		
		final_price = 0

		for module_id in modules_ids:
			module_obj = ModuleDetails.objects.get(id=module_id)
			remaining_price = 0

			if subscription.subscription_type == "WEEK":
				module_price = module_obj.weekly_price
				remaining_price = (module_price / 7)* remaining_days
			elif subscription.subscription_type == "MONTH":
				module_price = module_obj.monthly_price
				remaining_price = (module_price/30)* remaining_days
			elif subscription.subscription_type == "YEAR":
				module_price = module_obj.yearly_price
				remaining_price = (module_price/365)* remaining_days

			final_price = final_price + remaining_price
		
		for bundle_id in bundle_ids:
			bundle_obj = BundleDetails.objects.get(id=bundle_ids)

			if subscription.subscription_end_date == "WEEK":
				bundle_price = bundle_obj.weekly_price
				remaining_price = (bundle_price/7) * remaining_days
			elif subscription.subscription_type == "MONTH":
				bundle_price = bundle_obj.monthly_price
				remaining_price = (bundle_price/30)* remaining_days
			elif subscription.subscription_type == "YEAR":
				bundle_price = bundle_obj.yearly_price
				remaining_price = (bundle_price/365)* remaining_days


		response_dict["final_price"] = final_price
		response_dict["subscription_type"] = subscription.subscription_type
		response_dict["subscription_end_date"] = subscription_end_date

		return Response(response_dict, status=status.HTTP_200_OK)



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
		if billing_id:
			billing = BillingDetails.objects.filter(id=billing_id, user=request.user).last()
			if billing:
				order.bill = billing
				order.company_name = billing.company_name
				order.address = billing.address
				order.billing_contact = billing.billing_contact
				order.issuing_country = billing.issuing_country
				order.legal_company_name = billing.legal_company_name
				order.tax_id = billing.tax_id
				order.save()

		if card_id:
			card = CardDetails.objects.filter(id=card_id, user=request.user).last()
			if card:
				order.card = card
				order.holder_name = card.holder_name
				order.card_number = card.card_number
				order.expiration_date = card.expiration_date
				order.ccv = card.ccv
				order.save()

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
			intent = stripe.PaymentIntent.create(amount=round(order.total_price*100),currency='inr')
			payment_attempt=PaymentAttempt.objects.create(parchase_user_type="Subscription",parchase=order,user=request.user,currency='inr',amount=order.total_price,
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

			if payment_attempt.status != "succeeded":
				PaymentAttempt.objects.filter(payment_intent_id=intent['id']).update(
					last_payment_json=json.dumps(event)
				)
				payment_attempt.status='succeeded'
				
				try:
					if intent.get('charges'):
						payment_attempt.charges_json=json.dumps(intent.get('charges'))
						payment_attempt.total_charge=sum(i['amount'] for i in intent.get('charges').get('data'))
				except:
					pass
				order=payment_attempt.parchase
				payment_attempt.save()
				order.status='Placed'

				try:
					if intent.get('amount_received'):
						order.received_amounts=intent.get('amount_received')/100
				except:
					pass

				order.payment_dates=timezone.now()
				order.save()
				
				if order.parchase_user_type !="User":
					user = order.user
					user.is_subscribed = True
					user.free_subscribed = False
					user.free_subscription_end_date = timezone.now().date()
					user.save()
					if SubscriptionDetails.objects.filter(user=order.user):
						subscription = SubscriptionDetails.objects.filter(user=order.user).last()
						subscription.subscription_start_date = order.subscription_start_date
						subscription.subscription_end_date = order.subscription_end_date
						subscription.subscription_type =order.subscription_type
						subscription.is_subscribed = True
						subscription.module.clear()
						subscription.bundle.clear()
						if order.module:
							subscription.module.add(*list(order.module.values_list("id", flat=True)))      
						if order.bundle:
							subscription.bundle.add(*list(order.bundle.values_list("id", flat=True)))    
						subscription.save()
						try:
							module_list = list(order.module.values_list("id", flat=True))
							for i in module_list:
								FreeSubscriptionDetails.objects.filter(user=user, module__id=i).update(
									free_subscription_end_date=timezone.now().date() - timedelta(days=1)
								)
						except Exception as e:
							print(f"An error occurred: {e}")
						
					
					else:
						subscription = SubscriptionDetails.objects.create(
							user=order.user,
							subscription_start_date=order.subscription_start_date,
							subscription_end_date=order.subscription_end_date,
							is_subscribed=True,
							subscription_type=order.subscription_type,
						)
						if order.module:
							subscription.module.add(*list(order.module.values_list("id", flat=True)))      
						if order.bundle:
							subscription.bundle.add(*list(order.bundle.values_list("id", flat=True)))     
						subscription.save()
						try:
							module_list = list(order.module.values_list("id", flat=True))
							for i in module_list:
								FreeSubscriptionDetails.objects.filter(user=user, module__id=i).update(
									free_subscription_end_date=timezone.now().date() - timedelta(days=1)
								)
						except Exception as e:
							print(f"An error occurred: {e}")
				else:
					user = order.user
					user_subscription = UserSubscriptionDetails.objects.filter(
						user=order.user, 
					).last()
					if not user_subscription:
						subscription = UserSubscriptionDetails.objects.create(
							user=user,
							current_purchase=order,
							total_price=order.total_price,
							user_count=order.user_count,
							subscription_start_date=order.subscription_start_date,
							subscription_end_date=order.subscription_end_date,
							is_subscribed=True,
							subscription_type=order.subscription_type,
						)
						first_count_users = UserProfile.objects.filter(
							created_admin=user,
							is_active=True,
							is_free_user=False,
							subscription_end_date__lt=timezone.now().date()
						).order_by("-id")[:order.user_count]
						UserProfile.objects.filter(
							id__in=first_count_users.values_list("id", flat=True)
						).update(
							subscription_start_date=order.subscription_start_date,
							subscription_end_date=order.subscription_end_date
						)
						user.total_users = user.total_users + order.user_count
						user.available_paid_users = order.user_count
						user.save()
					elif order.action_type == "count_upgrade":
						user_subscription.current_purchase = order
						user_subscription.total_price = order.total_price
						user_subscription.user_count = user_subscription.user_count + order.user_count
						user_subscription.subscription_start_date = order.subscription_start_date
						user_subscription.subscription_end_date = order.subscription_end_date
						user_subscription.subscription_type =order.subscription_type
						user_subscription.save()
						first_count_users = list(UserProfile.objects.filter(
							created_admin=user,
							is_active=True,
							is_free_user=False,
						).order_by("-id")[:user_subscription.user_count].values_list("id", flat=True))
						UserProfile.objects.filter(
							id__in=first_count_users
						).update(
							subscription_start_date=order.subscription_start_date,
							subscription_end_date=order.subscription_end_date
						)
						user.total_users = user.total_users + order.user_count
						user.available_paid_users = user.available_paid_users + order.user_count
						user.save()
					
					elif order.action_type == "plan_upgrade":
						user_subscription.current_purchase = order
						user_subscription.total_price = order.total_price
						user_subscription.subscription_type =order.subscription_type
						user_subscription.is_subscribed = True
						user_subscription.subscription_start_date = order.subscription_start_date
						user_subscription.subscription_end_date = order.subscription_end_date
						user_subscription.save()
						first_count_users = (UserProfile.objects.filter(
							created_admin=user,
							is_active=True,
							is_free_user=False,
						).order_by("-id")[:user_subscription.user_count].values_list("id", flat=True))
						UserProfile.objects.filter(
							id__in=first_count_users
						).update(
							subscription_start_date=order.subscription_start_date,
							subscription_end_date=order.subscription_end_date
						)

					elif order.action_type == "both_upgrade":
						user_subscription.current_purchase = order
						user_subscription.total_price = order.total_price
						user_subscription.subscription_type =order.subscription_type
						user_subscription.user_count = user_subscription.user_count + order.user_count
						user_subscription.is_subscribed = True
						user_subscription.subscription_start_date = order.subscription_start_date
						user_subscription.subscription_end_date = order.subscription_end_date
						user_subscription.save()
						first_count_users = list(UserProfile.objects.filter(
							created_admin=user,
							is_active=True,
							is_free_user=False,
						).order_by("-id")[:user_subscription.user_count].values_list("id", flat=True))
						UserProfile.objects.filter(
							id__in=first_count_users
						).update(
							subscription_start_date=order.subscription_start_date,
							subscription_end_date=order.subscription_end_date
						)
						user.total_users = user.total_users + order.user_count
						user.available_paid_users = user.available_paid_users + order.user_count
						user.save()

					elif order.action_type == "renew":
						user_subscription.current_purchase = order
						user_subscription.total_price = order.total_price
						user_subscription.subscription_type =order.subscription_type
						user_subscription.is_subscribed = True
						user_subscription.subscription_start_date = order.subscription_start_date
						user_subscription.subscription_end_date = order.subscription_end_date
						user_subscription.save()
						first_count_users = list(UserProfile.objects.filter(
							created_admin=user,
							is_active=True,
							is_free_user=False,
						).order_by("-id")[:user_subscription.user_count].values_list("id", flat=True))
						UserProfile.objects.filter(
							id__in=first_count_users
						).update(
							subscription_start_date=order.subscription_start_date,
							subscription_end_date=order.subscription_end_date
						)


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
			intent = stripe.PaymentIntent.create(amount=round(order.total_price*100),currency='inr')
			payment_attempt=PaymentAttempt.objects.create(parchase_user_type="User",parchase=order,user=request.user,currency='inr',amount=order.total_price,
				status='Initiated',client_secret=intent['client_secret'],payment_intent_id=intent['id'],last_attempt_date=timezone.now())
		
			response_dict['client_secret']=payment_attempt.client_secret
			response_dict['status']=True
		return Response(response_dict,status.HTTP_200_OK)
	



class MockInitiatePayment(APIView):
	permission_classes = (IsAuthenticated,)
	authentication_classes = (CustomTokenAuthentication,)

	def post(self,request):
		response_dict={'status':False}
		try:
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

			if billing_id:
				billing = BillingDetails.objects.filter(id=billing_id, user=request.user).last()
				if billing:
					order.bill = billing
					order.company_name = billing.company_name
					order.address = billing.address
					order.billing_contact = billing.billing_contact
					order.issuing_country = billing.issuing_country
					order.legal_company_name = billing.legal_company_name
					order.tax_id = billing.tax_id
					order.save()

			if card_id:
				card = CardDetails.objects.filter(id=card_id, user=request.user).last()
				if card:
					order.card = card
					order.holder_name = card.holder_name
					order.card_number = card.card_number
					order.expiration_date = card.expiration_date
					order.ccv = card.ccv
					order.save()

			if modules_ids:
				for module_id in modules_ids:
					order.module.add(module_id)
			if bundle_ids:
				for bundle_id in bundle_ids:
					order.bundle.add(bundle_id)
   
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

			user = order.user
			user.is_subscribed = True
			if user.free_subscribed:
				user.free_subscription_end_date = timezone.now().date()
			user.free_subscribed = False
			user.save()

			if SubscriptionDetails.objects.filter(user=order.user):
				subscription = SubscriptionDetails.objects.filter(user=order.user).last()
				if subscription.subscription_end_date < timezone.now().date():
					subscription.subscription_start_date = order.subscription_start_date
					subscription.subscription_end_date = order.subscription_end_date
					subscription.is_subscribed = True
					subscription.user.is_subscribed = True
					subscription.module.clear()
					subscription.bundle.clear()
					if order.module:
						subscription.module.add(*list(order.module.values_list("id", flat=True)))      
					if order.bundle:
						subscription.bundle.add(*list(order.bundle.values_list("id", flat=True)))    
					subscription.save()
				else:
					if modules_ids:
						subscription.module.add(*list(order.module.values_list("id", flat=True)))      
					if bundle_ids:
						subscription.bundle.add(*list(order.bundle.values_list("id", flat=True)))    
			else:
				subscription = SubscriptionDetails.objects.create(
					user=order.user,
					subscription_start_date=order.subscription_start_date,
					subscription_end_date=order.subscription_end_date,
					is_subscribed=True,
					subscription_type=subscription_type
				)
				if modules_ids:
					subscription.module.add(*list(order.module.values_list("id", flat=True))) 
				if bundle_ids:				
					subscription.bundle.add(*list(order.bundle.values_list("id", flat=True)))

			with transaction.atomic():
				payment_attempt=PaymentAttempt.objects.create(parchase_user_type="Subscription",parchase=order,user=request.user,currency='inr',amount=order.total_price,
					status='succeeded',last_attempt_date=timezone.now())
				response_dict['purchase-id']=payment_attempt.id
				response_dict['status']=True
				response_dict["user-data"] = request.user.is_subscribed
				return Response(response_dict,status.HTTP_200_OK)
		except Exception as e:
			response_dict['error'] = str(e)
			return Response(response_dict, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class InitiateUserPaymentV2(APIView):
	permission_classes = (IsAuthenticated,)
	authentication_classes = (CustomTokenAuthentication,)

	def post(self,request):
		response_dict={'status':False}
		billing_id = request.data.get("billing_id")
		card_id = request.data.get("card_id")
		user_count = request.data.get("user_count")
		total_price = request.data.get("total_price")
		subscription_type = request.data.get("subscription_type")
		action_type = request.data.get("action_type")

		admin_subscription = UserSubscriptionDetails.objects.filter(
			user=request.user, 
		).last()
		current_date = datetime.now().date()
		if action_type == "renew":            
			subscription_type = admin_subscription.subscription_type
			if subscription_type == "WEEK":
				if admin_subscription.subscription_end_date < current_date:
					subscription_end_date = current_date
				else:
					subscription_end_date = admin_subscription.subscription_end_date
				subscription_end_date = subscription_end_date + timedelta(days=7)
			elif subscription_type == "MONTH":
				if admin_subscription.subscription_end_date < current_date:
					subscription_end_date = current_date
				else:
					subscription_end_date = admin_subscription.subscription_end_date
				subscription_end_date = subscription_end_date + timedelta(days=30)
			elif subscription_type == "YEAR":
				if admin_subscription.subscription_end_date < current_date:
					subscription_end_date = current_date
				else:
					subscription_end_date = admin_subscription.subscription_end_date
				subscription_end_date = subscription_end_date + timedelta(days=365)
			else:
				return Response({"error": "Invalid purchase duration"}, status=status.HTTP_400_BAD_REQUEST)
		elif action_type == "count_upgrade":
			subscription_end_date = admin_subscription.subscription_end_date
			t_user_count = admin_subscription.user_count
			user_count = user_count - t_user_count

		elif action_type == "plan_upgrade":
			if admin_subscription.subscription_type == subscription_type:
				subscription_end_date = admin_subscription.subscription_end_date
				if subscription_type == "WEEK":
					new_end_date = current_date + timedelta(days=7)
				elif subscription_type == "MONTH":
					new_end_date = current_date + timedelta(days=30)
				elif subscription_type == "YEAR":
					new_end_date = current_date + timedelta(days=365)
				subscription_end_date = new_end_date

			elif admin_subscription.subscription_type == "WEEK":
				if subscription_type == "MONTH":
					subscription_end_date = admin_subscription.subscription_end_date
					new_end_date = current_date + timedelta(days=30)
				elif subscription_type == "YEAR":
					subscription_end_date = admin_subscription.subscription_end_date
					new_end_date = current_date + timedelta(days=365)
				subscription_end_date = new_end_date
			elif admin_subscription.subscription_type == "MONTH":
				if subscription_type == "YEAR":
					subscription_end_date = admin_subscription.subscription_end_date
					new_end_date = current_date + timedelta(days=365)
				subscription_end_date = new_end_date

		elif action_type == "both_upgrade":
			t_user_count = admin_subscription.user_count
			user_count = user_count - t_user_count

			current_date = datetime.now().date()
			if admin_subscription.subscription_type == subscription_type:
				subscription_end_date = admin_subscription.subscription_end_date
				if subscription_type == "WEEK":
					new_end_date = current_date + timedelta(days=7)
				elif subscription_type == "MONTH":
					new_end_date = current_date + timedelta(days=30)
				elif subscription_type == "YEAR":
					new_end_date = current_date + timedelta(days=365)
				subscription_end_date = new_end_date

			elif admin_subscription.subscription_type == "WEEK":
				if subscription_type == "MONTH":
					subscription_end_date = admin_subscription.subscription_end_date
					new_end_date = current_date + timedelta(days=30)
				elif subscription_type == "YEAR":
					subscription_end_date = admin_subscription.subscription_end_date
					new_end_date = current_date + timedelta(days=365)
				subscription_end_date = new_end_date
			
			elif admin_subscription.subscription_type == "MONTH":
				if subscription_type == "YEAR":
					subscription_end_date = admin_subscription.subscription_end_date
					new_end_date = current_date + timedelta(days=365)
				subscription_end_date = new_end_date
		else:
			if subscription_type == "WEEK":
				subscription_end_date = current_date + timedelta(days=7)
			elif subscription_type == "MONTH":
				subscription_end_date = current_date + timedelta(days=30)
			elif subscription_type == "YEAR":
				subscription_end_date = current_date + timedelta(days=365)

		if admin_subscription:
			order = PurchaseDetails.objects.create(
				user=request.user,
				status="Pending",
				subscription_type=subscription_type,
				total_price=total_price,
				is_subscribed=False,
				subscription_end_date=subscription_end_date,
				subscription_start_date=admin_subscription.subscription_start_date,
				user_count=user_count,
				parchase_user_type="User",
				action_type=action_type
			)
		else:
			order = PurchaseDetails.objects.create(
				user=request.user,
				status="Pending",
				subscription_type=subscription_type,
				total_price=total_price,
				is_subscribed=False,
				subscription_end_date=subscription_end_date,
				subscription_start_date=timezone.now().date(),
				user_count=user_count,
				parchase_user_type="User",
				action_type=action_type
			)

		if billing_id:
			billing = BillingDetails.objects.filter(id=billing_id, user=request.user).last()
			if billing:
				order.bill = billing
				order.company_name = billing.company_name
				order.address = billing.address
				order.billing_contact = billing.billing_contact
				order.issuing_country = billing.issuing_country
				order.legal_company_name = billing.legal_company_name
				order.tax_id = billing.tax_id
				order.save()

		if card_id:
			card = CardDetails.objects.filter(id=card_id, user=request.user).last()
			if card:
				order.card = card
				order.holder_name = card.holder_name
				order.card_number = card.card_number
				order.expiration_date = card.expiration_date
				order.ccv = card.ccv
				order.save()

		with transaction.atomic():
			stripe.api_key=settings.STRIPE_API_KEY
			intent = stripe.PaymentIntent.create(amount=round(order.total_price*100),currency='inr')
			payment_attempt=PaymentAttempt.objects.create(parchase_user_type="User",parchase=order,user=request.user,currency='inr',amount=order.total_price,
				status='Initiated',client_secret=intent['client_secret'],payment_intent_id=intent['id'],last_attempt_date=timezone.now())
			response_dict['client_secret']=payment_attempt.client_secret
			response_dict['status']=True
		return Response(response_dict,status.HTTP_200_OK)


class InitiatePaymentV2(APIView):
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
		action_type = request.data.get("action_type")
		
		order = PurchaseDetails.objects.create(
			user=request.user,
			status="Pending",
			subscription_type=subscription_type,
			total_price=total_price,
			is_subscribed=False,
			action_type=action_type
		)
		if billing_id:
			billing = BillingDetails.objects.filter(id=billing_id, user=request.user).last()
			if billing:
				order.bill = billing
				order.company_name = billing.company_name
				order.address = billing.address
				order.billing_contact = billing.billing_contact
				order.issuing_country = billing.issuing_country
				order.legal_company_name = billing.legal_company_name
				order.tax_id = billing.tax_id
				order.save()

		if card_id:
			card = CardDetails.objects.filter(id=card_id, user=request.user).last()
			if card:
				order.card = card
				order.holder_name = card.holder_name
				order.card_number = card.card_number
				order.expiration_date = card.expiration_date
				order.ccv = card.ccv
				order.save()

		if modules_ids:
			order.module.add(*request.data.get("modules_ids"))    
		if bundle_ids:  
			order.bundle.add(*request.data.get("bundle_ids"))    

		subscription = SubscriptionDetails.objects.filter(
			user=order.user, 
		).last()
		admin_subscription = subscription
		current_date = datetime.now().date()
		if action_type == "renew":   
			order.subscription_start_date =  admin_subscription.subscription_start_date
			subscription_type = admin_subscription.subscription_type
			if subscription_type == "WEEK":
				if admin_subscription.subscription_end_date < current_date:
					subscription_end_date = current_date
				else:
					subscription_end_date = admin_subscription.subscription_end_date
				subscription_end_date = subscription_end_date + timedelta(days=7)
			elif subscription_type == "MONTH":
				if admin_subscription.subscription_end_date < current_date:
					subscription_end_date = current_date
				else:
					subscription_end_date = admin_subscription.subscription_end_date
				subscription_end_date = subscription_end_date + timedelta(days=30)
			elif subscription_type == "YEAR":
				if admin_subscription.subscription_end_date < current_date:
					subscription_end_date = current_date
				else:
					subscription_end_date = admin_subscription.subscription_end_date
				subscription_end_date = subscription_end_date + timedelta(days=365)
		elif action_type == "module_bundle_upgrade":
			order.subscription_start_date =  admin_subscription.subscription_start_date
			subscription_end_date = admin_subscription.subscription_end_date
		elif action_type == "plan_upgrade":
			order.subscription_start_date =  admin_subscription.subscription_start_date
			if admin_subscription.subscription_type == subscription_type:
				subscription_end_date = admin_subscription.subscription_end_date
				if subscription_type == "WEEK":
					new_end_date = current_date + timedelta(days=7)
				elif subscription_type == "MONTH":
					new_end_date = current_date + timedelta(days=30)
				elif subscription_type == "YEAR":
					new_end_date = current_date + timedelta(days=365)
				subscription_end_date = new_end_date
			elif admin_subscription.subscription_type == "WEEK":
				if subscription_type == "MONTH":
					subscription_end_date = admin_subscription.subscription_end_date
					new_end_date = current_date + timedelta(days=30)
				elif subscription_type == "YEAR":
					subscription_end_date = admin_subscription.subscription_end_date
					new_end_date = current_date + timedelta(days=365)
				subscription_end_date = new_end_date
			elif admin_subscription.subscription_type == "MONTH":
				if subscription_type == "YEAR":
					subscription_end_date = admin_subscription.subscription_end_date
					new_end_date = current_date + timedelta(days=365)
				subscription_end_date = new_end_date

		elif action_type == "both_upgrade":
			order.subscription_start_date =  admin_subscription.subscription_start_date
			if admin_subscription.subscription_type == subscription_type:
				subscription_end_date = admin_subscription.subscription_end_date
				if subscription_type == "WEEK":
					new_end_date = current_date + timedelta(days=7)
				elif subscription_type == "MONTH":
					new_end_date = current_date + timedelta(days=30)
				elif subscription_type == "YEAR":
					new_end_date = current_date + timedelta(days=365)
				subscription_end_date = new_end_date

			elif admin_subscription.subscription_type == "WEEK":
				if subscription_type == "MONTH":
					subscription_end_date = admin_subscription.subscription_end_date
					new_end_date = current_date + timedelta(days=30)
				elif subscription_type == "YEAR":
					subscription_end_date = admin_subscription.subscription_end_date
					new_end_date = current_date + timedelta(days=365)
				subscription_end_date = new_end_date
			
			elif admin_subscription.subscription_type == "MONTH":
				if subscription_type == "YEAR":
					subscription_end_date = admin_subscription.subscription_end_date
					new_end_date = current_date + timedelta(days=365)
				subscription_end_date = new_end_date
		else:
			order.subscription_start_date =  timezone.now().date()
			if subscription_type == "WEEK":
				subscription_end_date = current_date + timedelta(days=7)
			elif subscription_type == "MONTH":
				subscription_end_date = current_date + timedelta(days=30)
			elif subscription_type == "YEAR":
				subscription_end_date = current_date + timedelta(days=365)

		order.subscription_end_date =  subscription_end_date
		order.save()

		with transaction.atomic():
			stripe.api_key=settings.STRIPE_API_KEY
			intent = stripe.PaymentIntent.create(amount=round(order.total_price*100),currency='inr')
			payment_attempt=PaymentAttempt.objects.create(parchase_user_type="Subscription",parchase=order,user=request.user,currency='inr',amount=order.total_price,
				status='Initiated',client_secret=intent['client_secret'],payment_intent_id=intent['id'],last_attempt_date=timezone.now())
		
			response_dict['client_secret']=payment_attempt.client_secret
			response_dict['status']=True
		return Response(response_dict,status.HTTP_200_OK)