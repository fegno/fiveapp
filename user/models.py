from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from datetime import date
import random, string
from datetime import datetime, timedelta



USER_TYPE_CHOICES = (
    ("SUPER_ADMIN", "Super Admin"),
    ("ADMIN", "Admin"),
    ("USER", "User")
)


class UserProfile(AbstractUser):
    # username
    # email
    # password
    # first_name
    user_type = models.CharField(
        max_length=50, null=False, blank=True, choices=USER_TYPE_CHOICES, default="SUPER_ADMIN"
    )
    mobile_no = models.CharField(
        max_length=30, verbose_name="Mobile number", null=True, blank=True
    )
    company_name = models.CharField(max_length=100, blank=True, null=True)
    industrial_size = models.CharField(max_length=100, blank=True, null=True)
    employee_position = models.CharField(max_length=100, blank=True, null=True)

    available_free_users = models.IntegerField(default=5)
    available_paid_users = models.IntegerField(default=0)
    total_users = models.IntegerField(default=5)
    is_free_user = models.BooleanField(null=True, blank=True, default=False)
    is_subscribed = models.BooleanField(null=True, blank=True, default=False)

    subscription_start_date = models.DateField(null=True, blank=True)
    subscription_end_date = models.DateField(null=True, blank=True)
    parchase_id = models.IntegerField(null=True, blank=True)

    free_subscription_start_date = models.DateField(null=True, blank=True)
    free_subscription_end_date = models.DateField(null=True, blank=True)
    free_subscribed = models.BooleanField(null=True, blank=True, default=False)
    take_free_subscription = models.BooleanField(null=True, blank=True, default=False)

    created_admin =  models.ForeignKey(
        "self",
        blank=True,
        null=True,
        on_delete=models.CASCADE,  
    )
    is_active = models.BooleanField(null=False, blank=True, default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.username
    
    def start_free_trial(self):

        self.free_subscription_start_date = datetime.now().date()
        self.free_subscription_end_date = self.free_subscription_start_date + timedelta(days=15)  
        self.take_free_subscription = True
        self.free_subscribed = True
        self.save()


class Token(models.Model):
    key = models.CharField(max_length=40, unique=True)
    user = models.OneToOneField(
        UserProfile,
        related_name="auth_token",
        on_delete=models.CASCADE,
        unique=True,
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    session_dict = models.TextField(null=False, default="{}")

    dict_ready = False
    data_dict = None

    def __init__(self, *args, **kwargs):
        self.dict_ready = False
        self.data_dict = None
        super(Token, self).__init__(*args, **kwargs)

    def generate_key(self):
        return "".join(
            random.choice(
                string.ascii_lowercase + string.digits + string.ascii_uppercase
            )
            for i in range(40)
        )

    def save(self, *args, **kwargs):
        if not self.key:
            new_key = self.generate_key()
            while type(self).objects.filter(key=new_key).exists():
                new_key = self.generate_key()
            self.key = new_key
        return super(Token, self).save(*args, **kwargs)

    def read_session(self):
        if self.session_dict == "null":
            self.data_dict = {}
        else:
            self.data_dict = json.loads(self.session_dict)
        self.dict_ready = True

    def update_session(self, tdict, save=True, clear=False):
        if not clear and not self.dict_ready:
            self.read_session()
        if clear:
            self.data_dict = tdict
            self.dict_ready = True
        else:
            for key, value in tdict.items():
                self.data_dict[key] = value
        if save:
            self.write_back()

    def set(self, key, value, save=True):
        if not self.dict_ready:
            self.read_session()
        self.data_dict[key] = value
        if save:
            self.write_back()

    def write_back(self):
        self.session_dict = json.dumps(self.data_dict)
        self.save()

    def get(self, key, default=None):
        if not self.dict_ready:
            self.read_session()
        return self.data_dict.get(key, default)




class LoginOTP(models.Model):
    email = models.EmailField(max_length=100, null=True, blank=True)
    otp = models.IntegerField()
    is_verified = models.BooleanField(null=False, blank=True, default=False)
    user_type = models.CharField(
        max_length=50, null=False, blank=True, choices=USER_TYPE_CHOICES
    )
    
    def __str__(self):
        return self.email


class BillingDetails(models.Model):
    user = models.ForeignKey( UserProfile, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=150, null=True, blank=True)
    address = models.TextField(max_length=1000, null=True, blank=True)
    billing_contact = models.CharField(max_length=100, null=True, blank=True)
    issuing_country = models.CharField(max_length=100, null=True, blank=True)
    legal_company_name = models.CharField(max_length=100, null=True, blank=True)
    tax_id = models.CharField(max_length=12, null=True, blank=True)
    

    def __str__(self):
        return self.company_name
    

class CardDetails(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    holder_name = models.CharField(max_length=100, null=True, blank=True)
    card_number = models.CharField(max_length=20, null=True, blank=True)
    expiration_date = models.CharField(max_length=5, null=True, blank=True)
    ccv = models.CharField(max_length=3, null=True, blank=True)


class ForgotOTP(models.Model):
    email = models.EmailField(max_length=100, null=True, blank=True)
    otp = models.IntegerField()
    is_verified = models.BooleanField(null=False, blank=True, default=False)
    def __str__(self):
        return self.email
