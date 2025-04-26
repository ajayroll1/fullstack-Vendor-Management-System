from django.db import models
from django.utils.translation import gettext_lazy as _

from datetime import date


class Supplier(models.Model):

    supplier_name = models.CharField(max_length=255)
    mobile_no = models.CharField(max_length=10)
    address = models.TextField()
    datetime = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.supplier_name
    class meta:
       db_table = 'core_supplier'
       verbose_name = 'Supplier'  



class Item(models.Model):
    item_name = models.CharField(max_length=255)
    item_code = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.item_name



class SalesMaster(models.Model): 
    item = models.ForeignKey(Item, on_delete=models.CASCADE,default=1)
    customer_name = models.CharField(max_length=255)
    number = models.CharField(max_length=15)
    invoice_no = models.CharField(max_length=50, unique=True, blank=True)  # Allow blank initially
    invoice_date = models.DateField(default=date.today)   # Automatically set to current date
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    datetime = models.DateTimeField(auto_now_add=True)
    quantity = models.IntegerField(default=0)  # Add default=0
    price = models.DecimalField(max_digits=10, decimal_places=2 , default=0)  # Changed to DecimalField
    amount = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0)  # Auto-calculated

    def save(self, *args, **kwargs):
        # Generate invoice number if not provided
        if not self.invoice_no:  # Only generate if not set
            today = date.today()
            date_str = today.strftime("%Y-%m-%d")
            
            # Get the count of invoices for the same day and increment
            last_invoice = SalesMaster.objects.filter(invoice_no__startswith=date_str).order_by('-invoice_no').first()
            if last_invoice:
                last_serial = int(last_invoice.invoice_no.split("-")[-1])
                new_serial = last_serial + 1
            else:
                new_serial = 1

            self.invoice_no = f"{date_str}-{new_serial:02d}"  # Format serial as two digits
        
        # Ensure proper data types
        if isinstance(self.total_amount, str):
            self.total_amount = float(self.total_amount)
        if isinstance(self.quantity, str):
            self.quantity = int(self.quantity)
        if isinstance(self.price, str):
            self.price = float(self.price)
            
        # Calculate amount if quantity and price are set
        if self.quantity and self.price:
            self.amount = self.quantity * self.price

        super(SalesMaster, self).save(*args, **kwargs)  # Call the original save method

    def __str__(self):
        return f"{self.customer_name} - {self.invoice_no}"







class PurchaseMaster(models.Model):
    item = models.ForeignKey('Item', on_delete=models.CASCADE, default=1)  # Change '1' to an existing Item ID
    invoice_no = models.CharField(max_length=50, unique=True, blank=True)  # Allow blank initially
    invoice_date = models.DateField(default=date.today)  
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE )
    total_amount = models.FloatField()
    datetime = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return f"Invoice {self.invoice_no} - {self.total_amount}"

    def save(self, *args, **kwargs):
        # Ensure total_amount is properly saved as a float
        if isinstance(self.total_amount, str):
            self.total_amount = float(self.total_amount)
        super(PurchaseMaster, self).save(*args, **kwargs)




class PurchaseDetails(models.Model):
    item = models.ForeignKey('Item', on_delete=models.CASCADE, default=17)  # Set default=17 to match existing item
    quantity = models.IntegerField()
    price = models.FloatField()
    amount = models.FloatField()
    purchase_master = models.ForeignKey('PurchaseMaster', on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return f"Item {self.item.item_name} - {self.amount}"

    def save(self, *args, **kwargs):
        # Ensure amount is calculated properly
        if isinstance(self.quantity, str):
            self.quantity = int(self.quantity)
        if isinstance(self.price, str):
            self.price = float(self.price)
        
        # Calculate amount as quantity * price
        self.amount = float(self.quantity * self.price)
        
        super(PurchaseDetails, self).save(*args, **kwargs)








class BrandMaster(models.Model):
    brand_name = models.CharField(max_length=255, unique=True)
    status = models.BooleanField(default=True)  # Hidden field
    datetime = models.DateTimeField(auto_now_add=True)  # Hidden field

    def __str__(self):
        return self.brand_name







class SalesDetails(models.Model):
    item = models.ForeignKey('Item', on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.FloatField()
    amount = models.FloatField()
    sales_master = models.ForeignKey('SalesMaster', on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return f"Item {self.item.item_name} - {self.amount}"

    def save(self, *args, **kwargs):
        # Ensure amount is calculated properly
        if isinstance(self.quantity, str):
            self.quantity = int(self.quantity)
        if isinstance(self.price, str):
            self.price = float(self.price)
        
        # Calculate amount as quantity * price
        self.amount = float(self.quantity * self.price)
        
        super(SalesDetails, self).save(*args, **kwargs)






