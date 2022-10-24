from email.message import EmailMessage
# from logging import exception
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render,redirect
from cart.models import CartItem
from store.models import Product
from .forms import OrderForm
from .models import Order, OrderProduct, Payment
import datetime
import razorpay
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.contrib import messages
# Create your views here.


def place_order(request,total=0,quantity=0):
   current_user = request.user
   
#if the cart count<=0,then redirect to store 
   
   cart_items = CartItem.objects.filter(user=current_user)
   cart_count = cart_items.count()
   if cart_count <= 0:
        return redirect('store')
    
   grand_total = 0
   tax = 0
   for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
   tax = (2 * total)/100
   grand_total = total + tax
    
    
    
   if request.method == 'POST':
       form = OrderForm(request.POST)
       if form.is_valid():
           #store all the billing informationj inside order table
           
           data = Order()
           data.user = current_user
           data.first_name = form.cleaned_data['first_name']
           data.last_name = form.cleaned_data['last_name']
           data.phone = form.cleaned_data['phone']
           data.email = form.cleaned_data['email']
           data.address_line_1 = form.cleaned_data['address_line_1']
           data.address_line_2 = form.cleaned_data['address_line_2']
           data.country = form.cleaned_data['country']
           data.state = form.cleaned_data['state']
           data.city = form.cleaned_data['city']
           data.order_note = form.cleaned_data['order_note']
           data.pincode = form.cleaned_data['pincode']
           data.order_total = grand_total
           data.tax = tax
           data.ip = request.META.get('REMOTE_ADDR')
           data.save()
           #generate order_number
           
           year = int(datetime.date.today().strftime('%Y'))
           date = int(datetime.date.today().strftime('%d'))
           month = int(datetime.date.today().strftime('%m'))
           d = datetime.date(year,month,date)
           current_date = d.strftime("%Y%m%d")
           order_number = current_date + str(data.id)
           data.order_number = order_number
           data.save()
           
           
           order = Order.objects.get(user=current_user, order_number=order_number)
           order_number = order.order_number
           print(order_number)
           request.session['order_number'] = order_number
           
           return redirect('payments')
       else:
           return redirect('checkout')
       

@csrf_exempt
def success(request):
  order_number = request.session['order_number']
  transaction_id = Payment.objects.get(order_number=order_number)
  
  try:
      order = Order.objects.get(order_number=order_number)
      #when payment is success
      order.status = 'Shipped'
      order.save()
      
      ordered_products = OrderProduct.objects.filter(order_id=order.id)
      tax = 0
      total = 0
      grand_total = 0
      
      for item in ordered_products:
          
          total += (item.product_price * item.quantity)
      
      tax = total *2/100
      grand_total = total + tax
      
      context = {
          'order' : order,
          'ordered_products' : ordered_products,
          'transaction_id' : transaction_id,
          'tax' : tax,
          'total' : total,
          'grand_total' : grand_total,
        
      }
  except Exception as e:
      raise e
  return render(request,'orders/order_success.html',context)

def payment_failure(request):
    return render(request,'orders/order_failure.html')



def payments(request):
     total = 0
     current_user = request.user
     cart_item = CartItem.objects.filter(user=current_user)
     
     tax = 0
     grand_total = 0
     
     for item in cart_item:
         total += (item.product.price* item.quantity)
         
     tax = (2 * total) / 100
     grand_total = int(total) + int(tax)
     grand_total_razorpay = int(grand_total) * 100
     
     order_number = request.session['order_number']
     
     order = Order.objects.get(user=current_user,is_ordered=False,order_number=order_number)
     
     client = razorpay.Client(auth = (settings.RAZORPAY_KEY_ID , settings.RAZORPAY_SECRET_ID))
     payment = client.order.create({'amount':grand_total_razorpay , 'currency':'INR', 'payment_capture':1})
     order_id = payment['id']
     order_status = payment['status']
     if order_status == 'created':
        payDetails = Payment(
             user = current_user,
             order_id = order_id,
             order_number = order_number,
             amount_paid = order.order_total
         )
        payDetails.save()
      
     context = {
         'order_number' : order_number,
         'order_id': order_id,
         'payment' : payment,
         'order' : order,
         'cart_items' : cart_item,
         'total' : total,
         'tax' : tax,
         'grand_total' : grand_total,
         'razorpay_merchant_key' : settings.RAZORPAY_KEY_ID,
     }
     return render(request,'orders/payment.html',context)

@csrf_exempt
def payment_status(request):
    response = request.POST
    params_dict = {
        'razorpay_order_id' : response['razorpay_order_id'],
        'razorpay_payment_id' : response['razorpay_payment_id'],
        'razorpay_signature' : response['razorpay_signature']
    }   
    
    
    # authorize razorpay client with API keys.
    client = razorpay.Client(
        auth = (settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_ID))
    client = client
    try:
        status = client.utility.verify_payment_signature(params_dict)
        transaction = Payment.objects.get(order_id=response['razorpay_order_id'])
        transaction.status = status
        transaction.payment_id = response['razorpay_payment_id']
        transaction.save()
        
        # get order
        order_number = transaction.order_number
        order = Order.objects.get(order_number=order_number)
        order.payment = transaction
        order.is_ordered = True
        order.save()
        
        cart_items = CartItem.objects.filter(user=order.user)
        
        for item in cart_items:
            orderproduct = OrderProduct()
            orderproduct.order_id = order.id
            orderproduct.Payment = transaction
            orderproduct.user_id = order.user.id
            orderproduct.product_id = item.product_id
            orderproduct.quantity = item.quantity
            orderproduct.product_price = item.product.price
            orderproduct.ordered = True
            orderproduct.save()
            
            
            # Reducing Stock
            product = Product.objects.get(id=item.product_id)
            product.stock -= item.quantity
            product.save()
                    
             #  Clearing Cart Items
            # cart_item = CartItem.objects.get(id=item.id)
            # product_variation = cart_item.variations.all()
            # orderproduct = OrderProduct.objects.get(id=orderproduct.id)
            # orderproduct.variation.set(product_variation)
            # orderproduct.save()
            
        CartItem.objects.filter(user=order.user).delete()
            
        CartItem.objects.filter(user=order.user).delete()
        # current_site = get_current_site(request)
        # mail_subject = "Thank you for order!"
        # message = render_to_string('orders/order_recieved_email.html',{
        #     'user' : order.user,
        #     'order' : order,
        #     'domain' : current_site,
        # })
        # to_email = order.user.email
        # send_email = EmailMessage(mail_subject, message, to=[to_email])
        # send_email.send()
        
        # current_site=get_current_site(request)
        # mail_subject="please activate your account"
        # message= render_to_string('orders/order_recieved_email.html',{
        #     'user':order.user,
        #     'domain':current_site,
  
        # })
        # to_mail = order.user.email
        # send_email = EmailMessage(mail_subject, message, to=[to_mail])
        # send_email.send()
    
        return redirect('success')
    except Exception as e:
        raise e
        transaction = Payment.objects.get(order_id=response['razorpay_order_id'])
        transaction.delete()
        return redirect('payment_failure')