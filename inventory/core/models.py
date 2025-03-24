from django.db import models

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
        self.amount = self.quantity * self.price  # Auto-calculate amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item_name} - {self.quantity} x {self.price}"

    def save(self, *args, **kwargs):
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

        super().save(*args, **kwargs)  # Call the original save method

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




class PurchaseDetails(models.Model):
    item = models.ForeignKey('Item', on_delete=models.CASCADE)  # Changed from item_id to item
    quantity = models.IntegerField()
    price = models.FloatField()
    amount = models.FloatField()
    purchase_master = models.ForeignKey('PurchaseMaster', on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return f"Item {self.item.item_name} - {self.amount}"








class BrandMaster(models.Model):
    brand_name = models.CharField(max_length=255, unique=True)
    status = models.BooleanField(default=True)  # Hidden field
    datetime = models.DateTimeField(auto_now_add=True)  # Hidden field

    def __str__(self):
        return self.brand_name






