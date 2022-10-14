from django.db import models

from accounts.models import Account
from store.models import Product, Variation

# Create your models here.
class Payment(models.Model):
    user = models.ForeignKey(Account,on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=100, null=True)
    order_id = models.CharField(max_length=130,blank=True, null=True)
    order_number = models.CharField(max_length=100, blank=True, null=True)
    payment_method = models.CharField(max_length=100, null=True,default='RazorPay')
    amount_paid = models.CharField(max_length=100, null=True) #this is the total amount paid
    status = models.CharField(max_length=100, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    def __str__(self):
        return self.order_number
    

class Order(models.Model):
    STATUS = (
        ('New', 'New'),
        ('Accepted', 'Accepted'),
        ('completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    )
    
    user           = models.ForeignKey(Account,on_delete=models.SET_NULL,null=True)
    payment        = models.ForeignKey(Payment,on_delete=models.SET_NULL,blank=True,null=True)
    order_number   = models.CharField(max_length=20)
    first_name     = models.CharField(max_length=50)
    last_name      = models.CharField(max_length=50)
    phone          = models.CharField(max_length=15)
    email          = models.EmailField(max_length=50)
    address_line_1 = models.CharField(max_length=50)
    address_line_2 = models.CharField(max_length=50,blank=True)
    country        = models.CharField(max_length=50)
    state          = models.CharField(max_length=50)
    city           = models.CharField(max_length=50)
    order_note     = models.CharField(max_length=50,blank=True)
    pincode        = models.CharField(max_length=15,null=True)
    order_total    = models.FloatField()
    tax            = models.FloatField()
    status         = models.CharField(max_length=10,choices=STATUS,default='New')
    ip             = models.CharField(blank=True,max_length=20)
    is_ordered     = models.BooleanField(default=False)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True) 
    # razor_pay_order_id = models.CharField(max_length=100 , null=True, blank=True)
    # razor_pay_payment_id = models.CharField(max_length=100 , null=True, blank=True)
    # razor_pay_payment_signature = models.CharField(max_length=100 , null=True, blank=True)
    
    
    def full_name(self):
        return f'{self.first_name} {self.last_name}'
    
    def full_address(self):
        return f'{self.address_line_1} {self.address_line_2}'
    
    def __str__(self):
        return self. first_name
    

class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE,blank=True,null=True)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    variation = models.ForeignKey(Variation,on_delete=models.CASCADE)
    color = models.CharField(max_length=50)
    quantity = models.IntegerField()
    product_price = models.FloatField()
    ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    def __str__(self):
        return self.product.product_name 
    
    
    
        
