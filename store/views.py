from django.shortcuts import render
from .models import product

# Create your views here.

def store(request):
    products=product.objects.all().filter(is_available=True)
    product_count=products.count()
    
    context = {
        'products':products,
        'product_count':product_count
    }
    return render(request,'store/store.html',context)
