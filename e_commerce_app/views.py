from django.shortcuts import render, redirect
from django.contrib.auth.models import User, auth
from .models import Customer, Vendor, SoldItem, PurchasedItem, CartItem
from django.contrib import messages
from django.core.mail import send_mail
from main.settings import EMAIL_HOST_USER
import xlwt
from xlwt import Workbook
from django.core.files.storage import FileSystemStorage
import xlrd
from  django.http import  HttpResponse

def Index(request):
    return render(request, 'Index.html')

def CustomerLogin(request):
    return render(request, 'CustomerLogin.html')

def CustomerSignUp(request):
    return render(request,'CustomerSignUp.html')

def VendorLogin(request):
    return render(request, 'VendorLogin.html')

def VendorSignUp(request):
    return render(request,'VendorSignUp.html')

def CreateVendor(request):
    username=request.POST['username']
    email=request.POST['email']
    password1=request.POST['password1']
    password2=request.POST['password2']
    
    if(password1==password2):

        if User.objects.filter(username=username).exists():
            return render(request,'VendorSignUp.html',{"message":"Username already exists"})

        else:
            user=User.objects.create_user(username=username, password=password1)
            user.save()

            vendor=Vendor(username=username, email=email)
            vendor.save()

            user=auth.authenticate(username=username,password=password1)
            auth.login(request,user)
            return redirect('/VendorHome')
            
    else:
        return render(request,'VendorSignUp.html',{"message":"Passwords Do Not Match"})

def CreateCustomer(request):
    
    username=request.POST['username']
    password1=request.POST['password1']
    password2=request.POST['password2']
    
    if(password1==password2):

        if User.objects.filter(username=username).exists():
            return render(request,'CustomerSignUp.html',{"message":"Username already exists"})

        else:
            user=User.objects.create_user(username=username, password=password1)
            user.save()

            customer=Customer(username=username)
            customer.save()

            user=auth.authenticate(username=username,password=password1)
            auth.login(request,user)
            return redirect('/CustomerHome')
            
    else:
        return render(request,'CustomerSignUp.html',{"message":"Passwords Do Not Match"})

def FindVendor(request):
    username=request.POST['username']
    password=request.POST['password']
    
    user=auth.authenticate(username=username,password=password)
    try:
        vendor=Vendor.objects.get(username=username)
    except:
        return render(request,'VendorLogin.html',{"message":"You are not a Vendor"})

    if user is not None:
        auth.login(request,user)
        return redirect('/VendorHome')

    else:

        return render(request,'VendorLogin.html',{"message":"invalid username or password"})

def FindCustomer(request):
    username=request.POST['username']
    password=request.POST['password']

    user=auth.authenticate(username=username,password=password)

    try:
        customer=Customer.objects.get(username=username)
    except:
        return render(request,'CustomerLogin.html',{"message":"You are not a Customer"})

    if user is not None:
        auth.login(request,user)
        return redirect('/CustomerHome')

    else:

        return render(request,'CustomerLogin.html',{"message":"invalid username or password"})

def Logout(request):
    auth.logout(request)
    return redirect('/')

def VendorHome(request):
    current_user=request.user
    vendor=Vendor.objects.get(username=current_user.username)
    items=SoldItem.objects.filter(vendor=vendor).order_by('id')

    if vendor is None:
        return render(request, 'Hackerman.html')

    return render(request, 'VendorHome.html', {'vendor':vendor, 'items':items})

def CustomerHome(request):
    current_user=request.user
    customer=Customer.objects.get(username=current_user.username)
    items=SoldItem.objects.all().order_by('-sold_quantity')

    if customer is None:
        return render(request, 'Hackerman.html')

    return render(request, 'CustomerHome.html', {'customer':customer, 'items':items})

def AddItemToCart(request):
    current_user=request.user
    item_id=request.POST['item_id']
    item=SoldItem.objects.get(id=item_id)
    requested_quantity=request.POST['requested_quantity']

    if int(requested_quantity) > item.available_quantity:
        messages.info(request, 'Item not available in requested quantity')
        return redirect('/CustomerHome')
    
    customer=Customer.objects.get(username=current_user.username)
    cartitems=CartItem.objects.filter(customer=customer)

    for cartitem in cartitems:
        if cartitem.item == item:
            current_user=request.user
            customer=Customer.objects.get(username=current_user.username)
            items=SoldItem.objects.all().order_by('sold_quantity')
            items.reverse()
            return render(request, 'CustomerHome.html', {'customer':customer, 'items':items, 'message':'Item Already in Cart'})
    cost=int(item.price) * int(requested_quantity)
    cart=CartItem(customer=customer, item=item, requested_quantity=requested_quantity, cost=cost)
    cart.save()

    return redirect('/CustomerHome')

def BuyItem(request):
    #recieved value is a CartItem id 
    current_user=request.user
    BoughtItem=request.POST['item_id']
    BoughtItem=CartItem.objects.get(id=BoughtItem)

    customer=Customer.objects.get(username=current_user.username)
    cart=CartItem.objects.filter(customer=customer)

    if BoughtItem.requested_quantity > BoughtItem.item.available_quantity:
        return render(request, 'Cart.html', {'items':cart, 'customer':customer, 'message':'requested quantity not available'})

    if BoughtItem.customer.wallet_balance < BoughtItem.item.price*BoughtItem.requested_quantity:
        return render(request, 'Cart.html', {'items':cart, 'customer':customer, 'message':'insufficient balance'})

    #if BoughtItem.customer.has_ordered_item == True:
    #    return render(request, 'Cart.html', {'items':cart, 'customer':customer, 'message':'cannot order 2 things at a time'})

    customer=Customer.objects.get(username=current_user.username)
    customer.wallet_balance = customer.wallet_balance - BoughtItem.item.price*BoughtItem.requested_quantity
    #customer.has_ordered_item=True
    customer.save()

    item=SoldItem.objects.get(id=BoughtItem.item.id)
    item.available_quantity = item.available_quantity - BoughtItem.requested_quantity
    item.sold_quantity = item.sold_quantity + BoughtItem.requested_quantity
    item.save()

    purchase=PurchasedItem(customer=customer, item=item, quantity=BoughtItem.requested_quantity, cost=item.price*BoughtItem.requested_quantity)
    purchase.save()

    subject = 'New Purchase of ' + item.name
    message = customer.username + ' purchased ' + str(BoughtItem.requested_quantity)+ ' ' +item.name
    recepient=BoughtItem.item.vendor.email

    send_mail(subject, message, EMAIL_HOST_USER, [recepient], fail_silently = False)

    BoughtItem.delete()

    return redirect('/CustomerOrderHistory')


def Cart(request):
    current_user=request.user
    customer=Customer.objects.get(username=current_user.username)
    cart=CartItem.objects.filter(customer=customer)
    
    return render(request, 'Cart.html', {'items':cart, 'customer':customer})

def AddItemToSell(request):
    current_user=request.user
    vendor=Vendor.objects.get(username=current_user.username)

    item=SoldItem(vendor=vendor, name=request.POST['name'], picture=request.FILES['picture'], price=request.POST['price'], description=request.POST['description'], available_quantity=request.POST['available_quantity'])
    item.save()

    return redirect('/VendorHome')

def AddItemInfo(request):
    current_user=request.user
    vendor=Vendor.objects.get(username=current_user.username)
    return render(request, 'AddItemInfo.html', {'vendor':vendor})

def DeleteItem(request):
    current_user=request.user
    vendor=Vendor.objects.get(username=current_user.username)
    item=request.POST['item_id']
    item=SoldItem.objects.get(id=item)

    if current_user.username == item.vendor.username:
        item.delete()

    return redirect('/VendorHome')

def RemoveFromCart(request):
    item=request.POST['item_id']
    item=CartItem.objects.get(id=item)
    item.delete()
    return redirect('/Cart')

def AddMoney(request):
    amount=request.POST['amount']
    current_user=request.user
    customer=Customer.objects.get(username=current_user.username)
    customer.wallet_balance = customer.wallet_balance + int(amount)
    customer.save()
    return redirect('/Cart')

def ChangeAddress(request):
    address=request.POST['address']
    current_user=request.user
    try:
        customer=Customer.objects.get(username=current_user.username)
        customer.address=address
        customer.save()
        return redirect('/Cart')
    except:
        vendor=Vendor.objects.get(username=current_user.username)
        vendor.address=address
        vendor.save()
        return redirect('/VendorHome')
    

def CustomerOrderHistory(request):
    current_user=request.user
    customer=Customer.objects.get(username=current_user.username)
    purchases=PurchasedItem.objects.filter(customer=customer)

    return render(request, 'CustomerOrderHistory.html', {'items':purchases, 'customer':customer})

def CompleteOrder(request):
    current_user=request.user
    customer=Customer.objects.get(username=current_user.username)
    item=request.POST['item_id']
    item=PurchasedItem.objects.get(id=int(item))
    item.order_complete=True
    customer.has_ordered_item=False
    item.save()
    customer.save()
    return redirect('/CustomerOrderHistory')

def ModifyCustomerProfilePicture(request):
    current_user=request.user
    customer=Customer.objects.get(username=current_user.username)
    customer.profile_picture=request.FILES['picture']
    customer.save()
    return redirect('/Cart')

def ModifyVendorProfilePicture(request):
    current_user=request.user
    vendor=Vendor.objects.get(username=current_user.username)
    vendor.profile_picture=request.FILES['picture']
    vendor.save()
    return redirect('/VendorHome')

def ViewOrders(request):
    current_user=request.user
    vendor=Vendor.objects.get(username=current_user.username)
    items=SoldItem.objects.filter(vendor=vendor)

    purchases=PurchasedItem.objects.none()

    for item in items:
        purchases=purchases|PurchasedItem.objects.filter(item=item)

    return render(request, 'Orders.html', {'vendor':vendor, 'items':purchases})

def FindUser(request):
    current_user=request.user

    try :
        vendor=Vendor.objects.get(username=current_user.username)
    except :
        vendor=None

    if vendor is not None :
        return redirect('/VendorHome')

    try :
        customer=Customer.objects.get(username=current_user.username)
    except :
        customer=None
        
    if customer is not None:
        return redirect('/CustomerHome')

    return redirect('/Home')


def Home(request):
    current_user=request.user
    return render(request, 'Home.html', {'current_user':current_user})

def CreateGoogleCustomer(request):
    current_user=request.user
    try :
        vendor=Vendor.objects.get(username=current_user.username)
    except :
        vendor=None

    if vendor is not None :
        return redirect('/VendorHome')
    #print('New User Created')

    customer=Customer(username=current_user.username, email=current_user.email)
    customer.save()
    return redirect('/CustomerHome')

def CreateGoogleVendor(request):
    current_user=request.user
    try :
        customer=Customer.objects.get(username=current_user.username)
    except :
        customer=None

    if customer is not None :
        return redirect('/CustomerHome')
    #print('New User Created')

    vendor=Vendor(username=current_user.username, email=current_user.email)
    vendor.save()
    return redirect('/VendorHome')

def GenerateReport(request):
    current_user=request.user
    vendor=Vendor.objects.get(username=current_user.username)

    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="orders.xls"'

    wb=xlwt.Workbook()
    sheet1=wb.add_sheet('Sheet 1')

    sheet1.write(0,0,'Customer')
    sheet1.write(0,1,'Item')
    sheet1.write(0,2,'Price')
    sheet1.write(0,3,'Quantity')
    sheet1.write(0,4,'Amount')
    sheet1.write(0,5,'Order Completed')

    i=1

    items=SoldItem.objects.filter(vendor=vendor)

    purchases=PurchasedItem.objects.none()

    for item in items:
        purchases=purchases|PurchasedItem.objects.filter(item=item)

    for purchase in purchases:
        sheet1.write(i,0,purchase.customer.username)
        sheet1.write(i,1,purchase.item.name)
        sheet1.write(i,2,purchase.item.price)
        sheet1.write(i,3,purchase.quantity)
        sheet1.write(i,4,purchase.cost)
        sheet1.write(i,5,purchase.order_complete)
        i=i+1

    file_name=vendor.username+'.xls'

    wb.save(response)



    #fs=FileSystemStorage()
    #fs.save(file_name, wb)

    vendor.order_history=file_name
    vendor.save()

    return (response)