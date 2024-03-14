from django.shortcuts import render,redirect,get_object_or_404
from django.views import View
from . models import Customer,Cloth,Order,Cart
from . forms import RegistrationForm,AuthenticateForm,ChangePasswordForm,UserProfileForm,AdminProfileForm
from django.contrib.auth.forms import AuthenticationForm,PasswordChangeForm
from django.contrib.auth import authenticate,login,logout,update_session_auth_hash
from django.http import JsonResponse
from .models import ContactMessage
from .forms import CustomerForm


from paypal.standard.forms import PayPalPaymentsForm
from django.conf import settings
import uuid
from django.urls import reverse

def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        # Save the data to the database
        contact_message = ContactMessage.objects.create(name=name, email=email, message=message)
        contact_message.save()

        # You can perform additional actions here, such as sending emails to the admin

        return JsonResponse({'status': 'success'})

    return render(request, 'core/contact.html') 

# Create your views here.
# def home(request):
#     return render(request, 'core/home.html')

# --- Clased Based View of Home ---
class HomeView(View):
    def get(self,request):
        return render(request, 'core/home.html')


def about(request):
    return render(request, 'core/about.html')


def contact(request):
    return render(request, 'core/contact.html')

# --- Function Based View of dog_categories---
# def dog_categories(request):
#     return render(request,'core/dog_categories.html')

#=========================================================================================================

#--- Class Based View of dog_categories ---
class MenCategoriesView(View):
    def get(self,request):
        men_category = Cloth.objects.filter(category='MEN')  # we are using filter function of queryset, that will filter those data whose category belongs to dog
        return render(request,'core/men_categories.html',{'men_category':men_category})


# --- Function Based View of cat_categories---
# def cat_categories(request):
#     return render(request,'core/cat_categories.html')

#--- Class Based View of cat_categories ---
class WomenCategoriesView(View):
    def get(self,request):
        women_category = Cloth.objects.filter(category='WOMEN')  # we are using filter function of queryset, that will filter those data whose category belongs to dog
        return render(request,'core/women_categories.html',{'women_category':women_category})


def kids_categories(request):
    return render(request,'core/kids_categories.html')

#=========================================================================================================
# def pet_details(request):
#     return render(request,'core/pet_details.html')

class ClothDetailView(View):
    def get(self,request,id):     # id = It will fetch id of particular pet 
        cloth = Cloth.objects.get(pk=id)

        #------ code for caculate percentage -----
        if cloth.discounted_price !=0:    # fetch discount price of particular pet
            percentage = int(((cloth.selling_price-cloth.discounted_price)/cloth.selling_price)*100)
        else:
            percentage = 0
        # ------ code end for caculate percentage ---------
            
        return render(request,'core/cloth_details.html',{'cloth':cloth,'percentage':percentage})


#============================== Registration ==========================================================


def registration(request):
    if not request.user.is_authenticated:
        if request.method == 'POST':
            mf = RegistrationForm(request.POST)
            if mf.is_valid():
                mf.save()
                return redirect('registration')    
        else:
            mf  = RegistrationForm()
        return render(request,'core/registration.html',{'mf':mf})
    else:
        return redirect('profile')


#============================== Login ==========================================================

def log_in(request):
    if not request.user.is_authenticated:  # check whether user is not login ,if so it will show login option
        if request.method == 'POST':       # otherwise it will redirect to the profile page 
            mf = AuthenticateForm(request,request.POST)
            if mf.is_valid():
                name = mf.cleaned_data['username']
                pas = mf.cleaned_data['password']
                user = authenticate(username=name, password=pas)
                if user is not None:
                    login(request, user)
                    return redirect('/')
        else:
            mf = AuthenticateForm()
        return render(request,'core/login.html',{'mf':mf})
    else:
        return redirect('profile')
    

#================================= Profile ====================================================

def profile(request):
    if request.user.is_authenticated:  # This check wheter user is login, if not it will redirect to login page
        if request.method == 'POST':
            if request.user.is_superuser == True:
                mf = AdminProfileForm(request.POST,instance=request.user)
            else:
                mf = UserProfileForm(request.POST,instance=request.user)
            if mf.is_valid():
                mf.save()
        else:
            if request.user.is_superuser == True:
                mf = AdminProfileForm(instance=request.user)
            else:
                mf = UserProfileForm(instance=request.user)
        return render(request,'core/profile.html',{'name':request.user,'mf':mf})
    else:                                                # request.user returns the username
        return redirect('login')


#================================= Logout ====================================================

def log_out(request):
    logout(request)
    return redirect('home')


#================================= Change Password =============================================


def changepassword(request):                                       # Password Change Form               
    if request.user.is_authenticated:                              # Include old password 
        if request.method == 'POST':                               
            mf =ChangePasswordForm(request.user,request.POST)
            if mf.is_valid():
                mf.save()
                update_session_auth_hash(request,mf.user)
                return redirect('profile')
        else:
            mf = ChangePasswordForm(request.user)
        return render(request,'core/changepassword.html',{'mf':mf})
    else:
        return redirect('login')
    

#=========================== Add TO Cart Section =================================================
    
def add_to_cart(request, id):    # This 'id' is coming from 'pet.id' which hold the id of current pet , which is passing through {% url 'addtocart' pet.id %} from pet_detail.html 
    if request.user.is_authenticated:
        product = Cloth.objects.get(pk=id) # product variable is holding data of current object which is passed through 'id' from parameter
        user=request.user                # user variable store the current user i.e steveroger
        Cart(user=user,product=product).save()  # In cart model current user i.e steveroger will save in user variable and current pet object will be save in product variable
        return redirect('clothdetails', id)       # finally it will redirect to pet_details.html with current object 'id' to display pet after adding to the cart
    else:
        return redirect('login')                # If user is not login it will redirect to login page

def view_cart(request):
    cart_items = Cart.objects.filter(user=request.user)      # cart_items will fetch product of current user, and show product available in the cart of the current user.
    total =0
    delhivery_charge =2000
    for item in cart_items:
        item.product.price_and_quantity_total = item.product.discounted_price * item.quantity
        total += item.product.price_and_quantity_total
    final_price= delhivery_charge + total
    return render(request, 'core/view_cart.html', {'cart_items': cart_items,'total':total,'final_price':final_price})


def add_quantity(request, id):
    product = get_object_or_404(Cart, pk=id)    # If the object is found, it returns the object. If not, it raises an HTTP 404 exception (Http404).
    product.quantity += 1                   
    product.save()
    return redirect('viewcart')

def delete_quantity(request, id):
    product = get_object_or_404(Cart, pk=id)
    if product.quantity > 1:
        product.quantity -= 1
        product.save()
    return redirect('viewcart')

def delete_cart(request,id):
    if request.method == 'POST':
        de = Cart.objects.get(pk=id)
        de.delete()
    return redirect('viewcart')


#===================================== Checkout ============================================


#===================================== Address ============================================

def address(request):
    if request.method == 'POST':
            print(request.user)
            mf =CustomerForm(request.POST)
            print('mf',mf)
            if mf.is_valid():
                user=request.user                # user variable store the current user i.e steveroger
                name= mf.cleaned_data['name']
                address= mf.cleaned_data['address']
                city= mf.cleaned_data['city']
                state= mf.cleaned_data['state']
                pincode= mf.cleaned_data['pincode']
                print(state)
                print(city)
                print(name)
                Customer(user=user,name=name,address=address,city=city,state=state,pincode=pincode).save()
                return redirect('address')           
    else:
        mf =CustomerForm()
        address = Customer.objects.filter(user=request.user)
        print(address)
    return render(request,'core/address.html',{'mf':mf,'address':address})

def delete_address(request,id):
    if request.method == 'POST':
        de = Customer.objects.get(pk=id)
        de.delete()
    return redirect('address')



from django.db.models import Sum

def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)
    total = cart_items.aggregate(total_price=Sum('product__discounted_price'))['total_price'] or 0
    delhivery_charge = 100
    final_price = total + delhivery_charge if total > 0 else 0  # Only add delivery charge if cart is not empty

    address = Customer.objects.filter(user=request.user)

    return render(request, 'core/checkout.html', {'cart_items': cart_items, 'total': total, 'final_price': final_price, 'address': address})






def payment(request):

    if request.method == 'POST':
        selected_address_id = request.POST.get('selected_address')


    cart_items = Cart.objects.filter(user=request.user)      # cart_items will fetch product of current user, and show product available in the cart of the current user.
    total =0
    delhivery_charge =2000
    for item in cart_items:
        item.product.price_and_quantity_total = item.product.discounted_price * item.quantity
        total += item.product.price_and_quantity_total
    final_price= delhivery_charge + total
    
    address = Customer.objects.filter(user=request.user)

    #================= Paypal Code ======================================
    
    host = request.get_host()   # Will fecth the domain site is currently hosted on.

    paypal_checkout = {
        'business': settings.PAYPAL_RECEIVER_EMAIL,
        'amount': final_price,
        'item_name': 'Cloth',
        'invoice': uuid.uuid4(),
        'currency_code': 'USD',
        'notify_url': f"http://{host}{reverse('paypal-ipn')}",
        'return_url': f"http://{host}{reverse('paymentsuccess', args=[selected_address_id])}",
        'cancel_url': f"http://{host}{reverse('paymentfailed')}",
    }

    paypal_payment = PayPalPaymentsForm(initial=paypal_checkout)

#==========================================================================================================
    return render(request, 'core/payment.html', {'cart_items': cart_items,'total':total,'final_price':final_price,'address':address,'paypal':paypal_payment})


    #=======================================================================
   

#===================================== Payment Success ============================================

def payment_success(request,selected_address_id):
    print('payment sucess',selected_address_id)   # we have fetch this id from return_url': f"http://{host}{reverse('paymentsuccess', args=[selected_address_id])}
                                                  # This id contain address detail of particular customer
    user =request.user
    customer_data = Customer.objects.get(pk=selected_address_id,)
    cart = Cart.objects.filter(user=user)
    for c in cart:
        Order(user=user,customer=customer_data,cloth=c.product,quantity=c.quantity).save()
        c.delete()
    return render(request,'core/payment_success.html')



#===================================== Payment Failed ============================================


def payment_failed(request):
    return render(request,'core/payment_failed.html')

#===================================== Order ====================================================

def order(request):
    ord=Order.objects.filter(user=request.user)
    return render(request,'core/order.html',{'ord':ord})

#========================================== Buy Now ========================================================
def buynow(request,id):
    cloth = Cloth.objects.get(pk=id)     # cart_items will fetch product of current user, and show product available in the cart of the current user.
    delhivery_charge =2000
    final_price= delhivery_charge + cloth.discounted_price
    
    address = Customer.objects.filter(user=request.user)

    return render(request, 'core/buynow.html', {'final_price':final_price,'address':address,'cloth':cloth})


def buynow_payment(request,id):

    if request.method == 'POST':
        selected_address_id = request.POST.get('buynow_selected_address')

    cloth = Cloth.objects.get(pk=id)     # cart_items will fetch product of current user, and show product available in the cart of the current user.
    delhivery_charge =2000
    final_price= delhivery_charge + cloth.discounted_price
    
    address = Customer.objects.filter(user=request.user)
    #================= Paypal Code ======================================

    host = request.get_host()   # Will fecth the domain site is currently hosted on.

    paypal_checkout = {
        'business': settings.PAYPAL_RECEIVER_EMAIL,
        'amount': final_price,
        'item_name': 'Cloth',
        'invoice': uuid.uuid4(),
        'currency_code': 'USD',
        'notify_url': f"http://{host}{reverse('paypal-ipn')}",
        'return_url': f"http://{host}{reverse('buynowpaymentsuccess', args=[selected_address_id,id])}",
        'cancel_url': f"http://{host}{reverse('paymentfailed')}",
    }

    paypal_payment = PayPalPaymentsForm(initial=paypal_checkout)

    #========================================================================

    return render(request, 'core/payment.html', {'final_price':final_price,'address':address,'cloth':cloth,'paypal':paypal_payment})

def buynow_payment_success(request,selected_address_id,id):
    print('payment sucess',selected_address_id)   # we have fetch this id from return_url': f"http://{host}{reverse('paymentsuccess', args=[selected_address_id])}
                                                  # This id contain address detail of particular customer
    user =request.user
    customer_data = Customer.objects.get(pk=selected_address_id,)
    
    cloth = Cloth.objects.get(pk=id)
    Order(user=user,customer=customer_data,cloth=cloth,quantity=1).save()
   
    return render(request,'core/buynow_payment_success.html')