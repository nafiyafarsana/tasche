# from orders.models import Order
from email.message import EmailMessage
from django.shortcuts import get_object_or_404, render,redirect
from .forms import RegistrationForm,UserForm,UserprofileForm
from .models import Account,UserProfile
from orders.models import Order, OrderProduct
from django.contrib import messages,auth
from django.contrib.auth.decorators import login_required 
from django.views.decorators.cache import never_cache
from cart.models import Cart,CartItem
import requests
from cart.views import _cart_id


# Create your views here.
# verification_email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

def register(request):
    if request.method=='POST':
        form=RegistrationForm(request.POST)
        if form.is_valid():
            first_name=form.cleaned_data['first_name']
            last_name=form.cleaned_data['last_name']
            phone_number=form.cleaned_data['phone_number']
            email=form.cleaned_data['email']
            password=form.cleaned_data['password']
            username=email.split("@")[0]
            
            user=Account.objects.create_user(first_name=first_name,last_name=last_name,email=email,username=username,password=password)
            user.phone_number=phone_number
            user.save()
            
            # user_activation
            current_site=get_current_site(request)
            mail_subject="please activate your account"
            message= render_to_string('accounts/account_verification_email.html',{
                'user':user,
                'domain':current_site,
                 'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                 'token':default_token_generator.make_token(user)
            })
            to_mail = email
            send_email = EmailMessage(mail_subject, message, to=[to_mail])
            send_email.send()
            # messages.success(request,"Thank You for registering with us.We have sent you a verification mail to your email address.Please verify it.")
            return redirect('/accounts/login/?command=verification&email='+email)
    else:
     form=RegistrationForm()
    context={
        'form':form,
    }
    return render(request,'accounts/register.html',context)
@never_cache
def login(request):
    if request.method=="POST":
        email=request.POST['email']
        password=request.POST['password']
        
        user=auth.authenticate(request,email=email,password=password)
        
        if user is not None:
            try:
                # print('entering inside try block')
                carts = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart=carts).exists()
                # print(is_cart_item_exists)
                if is_cart_item_exists:
                    cart_items = CartItem.objects.filter(cart=carts)
                    product_variation = []
                    for item in cart_items:
                        variation = item.variations.all()
                        product_variation.append(list(variation))
                        
                    #get the cart_item from the user to access his product variation
                    cart_items = CartItem.objects.filter(user=user)
                    ex_var_list = []
                    id = []
                    for item in cart_items:
                        existing_variation = item.variations.all()
                        ex_var_list.append(list(existing_variation))
                        id.append(item.id)
                        
                    #product_variation = [1,2,3,4,5]
                    #ex_var_list       = [4,6,3,5]
                    
                    for pr in product_variation:
                        if pr in ex_var_list:
                            index = ex_var_list.index(pr)
                            item_id = id[index]
                            item = CartItem.objects.get(id=item_id)
                            item.quantity += 1
                            item.user = user 
                            item.save()
                        else:
                            cart_items = CartItem.objects.filter(cart=carts)   
                    
                    for item in cart_items:
                        item.user = user
                        item.save()
            except:
                pass
            auth.login(request, user)
            messages.success(request,"you are now logged in")
            
            url = request.META.get('HTTP_REFERER')
            try:
                query = requests.utils.urlparse(url).query
                # next=/cart/checkout
                params = dict(x.split('=')for x in query.split('&'))
                if 'next' in params:
                    nextPage = params['next']
                    return redirect(nextPage)
                
            except:
                return redirect('home')   
        else:
            messages.error(request,"invlaid login credentials")
            return redirect('login')
            
    return render(request,'accounts/login.html' )
@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    messages.success(request,"logged out")
    return redirect('login')



def activate(request,uidb64,token):
    try:
        uid=urlsafe_base64_decode(uidb64).decode()
        user=Account._default_manager.get(pk=uid)
    except(TypeError,ValueError,OverflowError,Account.DoesNotExist):
        user=None
    if user is not None and default_token_generator.check_token(user,token):
        user.is_active=True
        user.save()
        messages.success(request,'Congratulations!your account is activated.')
        
        # Userprofile generation
        user_profile = UserProfile.objects.create(
            user = user,
            address_line_1 = "address 1",
            address_line_2 = "address 2"
        )
         
        user_profile.save()
        
        return redirect('login')
    else:
        messages.error(request,'invalid activation link')
        return redirect('register')
    
@login_required(login_url='login') 
def user_dashboard(request):
    orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id, is_ordered=True)
    orders_count = orders.count()
    
    userprofile = UserProfile.objects.get(user_id = request.user.id)
    context = {
        'orders_count': orders_count,
        'userprofile': userprofile,
    }
    return render(request, 'accounts/user_dashboard.html',context)

def forgotpassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__iexact=email)
           
           # Reset password email
            current_site = get_current_site(request)
            mail_subject = 'Reset Your Password'
            message = render_to_string('accounts/reset_password_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
          
            messages.success(request, 'Password reset email has been sent to your email address.')
            return redirect('login')
          
        else:
            messages.error(request, 'Account does not exist!')    
            return redirect('forgotpassword')
    return render(request, 'accounts/forgotpassword.html')

#   if request.method == 'POST':
#     email = request.POST['email']
#     try:
#       user = Account.objects.get(email=email, is_active=True)
      
#       # USER ACTIVATION
#       current_site = get_current_site(request)
#       mail_subject = "Reset Password"
#       message = render_to_string('accounts/forgot_password_email.html', {
#         'user': user,
#         'domain': current_site,
#         'uid': urlsafe_base64_encode(force_bytes(user.pk)),
#         'token': default_token_generator.make_token(user),
#       })
#       to_mail = email
#       send_email = EmailMessage(mail_subject, message, to=[to_mail])
#       send_email.send()
      
#       messages.success(request, 'Reset link has been sended to your verified email address')
#     except:
#       messages.error(request, 'Account not found')
  
#   return render(request, 'accounts/forgotpassword.html')

 

        
def resetpassword_validate(request,uidb64,token):
    try:
        uid=urlsafe_base64_decode(uidb64).decode()
        user=Account._default_manager.get(pk=uid)
    except(TypeError,ValueError,OverflowError,Account.DoesNotExist):
        user=None
    if user is not None and default_token_generator.check_token(user,token):
        request.session['uid']=uid
        messages.success(request,'please reset your password ')
        return redirect('resetpassword')
    else:
        messages.error(request,'this link has been expired!')
        return redirect('login')
    
def resetpassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST.get('confirm_password')
        
        if password == confirm_password:
            uid=request.session.get('uid')
            user=Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request,'password reset is successfull')
            return redirect('login')
            
        else:
            messages.error(request,'password do not match!')
            return redirect('resetpassword')
        
    else:
        return render(request,'accounts/resetpassword.html')
@login_required(login_url='login')    
def my_orders(request):
    orders = Order.objects.filter(user=request.user,is_ordered=True).order_by('created_at')
    context = {
        'orders' : orders,
    }
    return render(request,'accounts/my_orders.html',context)
    
    
def edit_profile(request):
    userprofile = get_object_or_404(UserProfile,user=request.user)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserprofileForm(request.POST, request.FILES, instance=userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('edit_profile')
    else:
      user_form =UserForm(instance=request.user)
      profile_form = UserprofileForm(instance=userprofile)
    context = {
        'user_form' : user_form,
        'profile_form' : profile_form,
        'userprofile' : userprofile,
        }
    return render(request,'accounts/edit_profile.html',context)
@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']
        
        user = Account.objects.get(username__exact=request.user.username)
        
        if new_password == confirm_password:
            success = user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()
                #auth.logout(request)
                messages.success(request, 'Password updated successfully.')
                return redirect('change_password')
            else:
                messages.error(request, 'Please enter valid current password')
                return redirect('change_password')
            
        else:
            messages.error(request, 'Password does not match!')
            return redirect('change_password')
        
    return render(request,'accounts/change_password.html')
@login_required(login_url='login')
def order_detail(request,order_id):
    order_detail =  OrderProduct.objects.filter(order__order_number=order_id)   
    order = Order.objects.get(order_number=order_id)
    
    total = 0
    tax = 0
    grand_total = 0
    for i in order_detail:
        total += i.product_price * i.quantity
        
    tax = 2*total / 100
    grand_total = total + tax

    
    # variations = Variation.objects.filter(variation_category=variation_category,variation_value=variation_value)
    context = {
        'order_detail' : order_detail,
        'order' : order, 
        
        'total':total,
        'tax':tax,
        'grand_total':grand_total

    }
    return render(request,'accounts/order_detail.html',context)
    