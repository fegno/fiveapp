from django.db import models
from administrator.models import PurchaseDetails
from user.models import UserProfile

PAYMENT_ATTEMPT_STATUS_CHOICES=(
	('Initiated','Initiated'),
	('requires_payment_method','requires_payment_method'),
	('requires_confirmation','requires_confirmation'),
	('requires_action','requires_action'),
	('processing','processing'),
	('Cancelled','Cancelled'),
	('succeeded','succeeded')
	
)

class PaymentAttempt(models.Model):
	parchase   =	models.ForeignKey(
        PurchaseDetails,
        null=True,
        related_name='payment_attempts',
        on_delete=models.CASCADE,   
    )
	user=	models.ForeignKey(UserProfile,related_name="payment_attempts", on_delete=models.CASCADE,   )
	payment_intent_id		=	models.CharField(max_length=255,null=True,blank=True)
	currency				=	models.CharField(null=False,blank=False,max_length=12,default='AED')
	amount					=	models.FloatField(null=False,blank=True)
	charges_json			=	models.TextField(null=True,blank=True)
	total_charge			=	models.FloatField(null=True,blank=True)
	client_secret			=	models.CharField(null=True,blank=True,max_length=255)
	description				=	models.TextField(null=True)
	last_payment_error_json	=	models.TextField(null=True)
	status					=	models.CharField(max_length=50,blank=True,null=False,db_index=True,choices=PAYMENT_ATTEMPT_STATUS_CHOICES)
	last_attempt_date		=	models.DateTimeField(null=True,blank=True)
	is_active				=	models.BooleanField(null=False,blank=True,default=True)
	created					=	models.DateTimeField(auto_now_add=True)
	updated					=	models.DateTimeField(auto_now=True)
	parchase_user_type		=	models.CharField(null=True,blank=True,max_length=255)
