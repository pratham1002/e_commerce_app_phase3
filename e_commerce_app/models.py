from django.db import models

class Vendor(models.Model):
    email=models.CharField(max_length=100)
    username=models.CharField(max_length=50)
    description=models.CharField(max_length=256)
    address=models.CharField(max_length=256)
    profile_picture=models.ImageField(upload_to='images/')
    is_vendor=models.BooleanField(default=True)
    is_customer=models.BooleanField(default=False)
    order_history=models.FileField(upload_to='images/')
    def __str__(self):
        return self.username

class Customer(models.Model):
    email=models.CharField(max_length=100)
    username=models.CharField(max_length=50)
    address=models.CharField(max_length=256)
    profile_picture=models.ImageField(upload_to='images/')
    wallet_balance=models.IntegerField(default=0)
    is_vendor=models.BooleanField(default=False)
    is_customer=models.BooleanField(default=True)
    has_ordered_item=models.BooleanField(default=False)
    def __str__(self):
        return self.username

class SoldItem(models.Model):
    vendor=models.ForeignKey(Vendor, on_delete=models.CASCADE)
    name=models.CharField(max_length=100)
    picture=models.ImageField(upload_to='images/')
    description=models.CharField(max_length=256)
    price=models.IntegerField(default=0)
    available_quantity=models.IntegerField(default=0)
    sold_quantity=models.IntegerField(default=0)
    is_still_sold=models.BooleanField(default=True)

class PurchasedItem(models.Model):
    customer=models.ForeignKey(Customer, on_delete=models.CASCADE)
    item=models.ForeignKey(SoldItem, on_delete=models.CASCADE)
    quantity=models.IntegerField(default=0)
    order_complete=models.BooleanField(default=False)
    cost=models.BigIntegerField(default=0)

class CartItem(models.Model):
    customer=models.ForeignKey(Customer, on_delete=models.CASCADE)
    item=models.ForeignKey(SoldItem, on_delete=models.CASCADE)
    requested_quantity=models.IntegerField(default=0)
    cost=models.IntegerField(default=0)


