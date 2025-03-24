from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import Supplier, SalesMaster, PurchaseMaster, Item, PurchaseDetails, BrandMaster
from .forms import SupplierForm, SalesMasterForm, PurchaseMasterForm, ItemForm, PurchaseDetailsForm, BrandMasterForm
from datetime import date, datetime
from django.db.models import Max
import csv
from django.db.models import Sum

def report(request):
    # Get all counts
    total_suppliers = Supplier.objects.count()
    total_sales = SalesMaster.objects.count()
    total_purchase = PurchaseMaster.objects.count()
    total_items = Item.objects.count()
    total_brands = BrandMaster.objects.count()
    
    # Calculate total stocks from purchase details
    total_stocks = PurchaseDetails.objects.filter(status=True).aggregate(total=Sum('quantity'))['total'] or 0
    
    # Calculate total sales amount
    total_sales_amount = SalesMaster.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Calculate total purchase amount
    total_purchase_amount = PurchaseMaster.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Calculate remaining stocks
    remaining_stocks = total_stocks - total_sales_amount
    
    # Calculate total available (remaining) stocks
    total_available = total_stocks - total_sales

    return render(request, 'report.html', {
        'total_suppliers': total_suppliers,
        'total_sales': total_sales_amount,
        'total_purchase': total_purchase_amount,
        'total_items': total_items,
        'total_brands': total_brands,
        'total_stocks': total_stocks,
        'total_sales_quantity': total_sales_amount,
        'remaining_stocks': remaining_stocks,
        'total_available': total_available
    })

def index(request):
    return render(request, 'index.html')

def supplier_list(request):
    suppliers = Supplier.objects.all()
    
    # Handle filtering
    name = request.GET.get('name')
    mobile = request.GET.get('mobile')
    address = request.GET.get('address')
    status = request.GET.get('status')
    
    if name:
        suppliers = suppliers.filter(supplier_name__icontains=name)
    if mobile:
        suppliers = suppliers.filter(mobile_no__icontains=mobile)
    if address:
        suppliers = suppliers.filter(address__icontains=address)
    if status:
        suppliers = suppliers.filter(status=status)
    
    # Handle CSV export
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="suppliers.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Name', 'Mobile No', 'Address', 'Status'])
        
        for supplier in suppliers:
            writer.writerow([
                supplier.id,
                supplier.supplier_name,
                supplier.mobile_no,
                supplier.address,
                'Active' if supplier.status else 'Inactive'
            ])
        
        return response
    
    return render(request, 'supplier_list.html', {'suppliers': suppliers})

def supplier_create(request):
    if request.method == "POST":
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Supplier added successfully.')
            return redirect('supplier_list')
        else:
            messages.error(request, 'Error adding supplier. Please check the form.')
    return redirect('supplier_list')

def supplier_edit(request, id):
    supplier = get_object_or_404(Supplier, id=id)
    if request.method == "POST":
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, 'Supplier updated successfully.')
            return redirect('supplier_list')
        else:
            messages.error(request, 'Error updating supplier. Please check the form.')
    return render(request, 'supplier_edit.html', {'supplier': supplier})

def supplier_delete(request, id):
    if request.method == "POST":
        supplier = get_object_or_404(Supplier, id=id)
        supplier.delete()
        messages.success(request, 'Supplier deleted successfully.')
    return redirect('supplier_list')

def sales_master_list(request):
    sales = SalesMaster.objects.all()
    items = Item.objects.all()
    suppliers = Supplier.objects.all()  # Get all suppliers
    
    # Handle filtering
    invoice_no = request.GET.get('invoice_no')
    customer = request.GET.get('customer')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if invoice_no:
        sales = sales.filter(invoice_no__icontains=invoice_no)
    if customer:
        sales = sales.filter(customer_name__icontains=customer)
    if date_from:
        sales = sales.filter(invoice_date__gte=date_from)
    if date_to:
        sales = sales.filter(invoice_date__lte=date_to)
    
    context = {
        'sales': sales,
        'items': items,
        'suppliers': suppliers,  # Add suppliers to context
    }
    return render(request, 'sales_master_list.html', context)

def generate_invoice_number(prefix):
    """Generate a sequential invoice number with prefix"""
    today = datetime.now()
    year = today.strftime('%Y')
    month = today.strftime('%m')
    
    # Get the last invoice number for this prefix and month
    if prefix == 'SALE':
        last_invoice = SalesMaster.objects.filter(
            invoice_no__startswith=f"{prefix}{year}{month}"
        ).order_by('-invoice_no').first()
    else:  # PURCHASE
        last_invoice = PurchaseMaster.objects.filter(
            invoice_no__startswith=f"{prefix}{year}{month}"
        ).order_by('-invoice_no').first()
    
    if last_invoice:
        last_number = int(last_invoice.invoice_no[-4:])
        new_number = last_number + 1
    else:
        new_number = 1
    
    return f"{prefix}{year}{month}{new_number:04d}"

def sales_master_create(request):
    if request.method == 'POST':
        invoice_no = generate_invoice_number('SALE')
        invoice_date = request.POST.get('invoice_date')
        total_amount = request.POST.get('total_amount')
        
        SalesMaster.objects.create(
            invoice_no=invoice_no,
            invoice_date=invoice_date,
            total_amount=total_amount
        )
        messages.success(request, 'Sales record created successfully!')
        return redirect('sales_master_list')
    return render(request, 'sales_master_create.html')

def sales_master_edit(request, id):
    sales = get_object_or_404(SalesMaster, id=id)
    if request.method == "POST":
        form = SalesMasterForm(request.POST, instance=sales)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sales record updated successfully.')
            return redirect('sales_master_list')
        else:
            messages.error(request, 'Error updating sales record. Please check the form.')
    return render(request, 'sales_master_edit.html', {'sales': sales})

def sales_master_delete(request, id):
    if request.method == "POST":
        sales = get_object_or_404(SalesMaster, id=id)
        sales.delete()
        messages.success(request, 'Sales record deleted successfully.')
    return redirect('sales_master_list')

def purchase_master_list(request):
    purchases = PurchaseMaster.objects.all()
    suppliers = Supplier.objects.all()
    items = Item.objects.all()  # Get all items
    
    # Handle filtering
    invoice_no = request.GET.get('invoice_no')
    supplier = request.GET.get('supplier')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if invoice_no:
        purchases = purchases.filter(invoice_no__icontains=invoice_no)
    if supplier:
        purchases = purchases.filter(supplier_id=supplier)
    if date_from:
        purchases = purchases.filter(invoice_date__gte=date_from)
    if date_to:
        purchases = purchases.filter(invoice_date__lte=date_to)
    
    context = {
        'purchases': purchases,
        'suppliers': suppliers,
        'items': items,  # Add items to context
    }
    return render(request, 'purchase_master_list.html', context)

def purchase_master_create(request):
    if request.method == 'POST':
        try:
            # Generate automatic invoice number
            today = date.today()
            date_str = today.strftime("%Y-%m-%d")
            last_invoice = PurchaseMaster.objects.filter(invoice_no__startswith=date_str).order_by('-invoice_no').first()
            if last_invoice:
                last_serial = int(last_invoice.invoice_no.split("-")[-1])
                new_serial = last_serial + 1
            else:
                new_serial = 1
            invoice_no = f"{date_str}-{new_serial:02d}"
            
            supplier_id = request.POST.get('supplier')
            total_amount = request.POST.get('total_amount')
            
            if supplier_id and total_amount:
                supplier = get_object_or_404(Supplier, id=supplier_id)
                # Create PurchaseMaster record
                purchase_master = PurchaseMaster.objects.create(
                    invoice_no=invoice_no,
                    invoice_date=today,
                    supplier=supplier,
                    total_amount=total_amount
                )
                
                # Handle purchase details
                items = request.POST.getlist('items[]')
                quantities = request.POST.getlist('quantities[]')
                prices = request.POST.getlist('prices[]')
                amounts = request.POST.getlist('amounts[]')
                
                for i in range(len(items)):
                    if items[i]:  # Only create if item is selected
                        item = get_object_or_404(Item, id=items[i])
                        PurchaseDetails.objects.create(
                            item=item,
                            quantity=quantities[i],
                            price=prices[i],
                            amount=amounts[i],
                            purchase_master=purchase_master
                        )
                
                messages.success(request, 'Purchase record created successfully!')
                return redirect('purchase_master_list')
            else:
                messages.error(request, 'Please fill all required fields.')
        except Exception as e:
            messages.error(request, f'Error creating purchase record: {str(e)}')
    
    suppliers = Supplier.objects.all()
    items = Item.objects.all()
    return render(request, 'purchase_master_create.html', {
        'suppliers': suppliers,
        'items': items
    })

def purchase_master_edit(request, id):
    purchase = get_object_or_404(PurchaseMaster, id=id)
    suppliers = Supplier.objects.all()
    if request.method == "POST":
        form = PurchaseMasterForm(request.POST, instance=purchase)
        if form.is_valid():
            form.save()
            messages.success(request, 'Purchase record updated successfully.')
            return redirect('purchase_master_list')
        else:
            messages.error(request, 'Error updating purchase record. Please check the form.')
    return render(request, 'purchase_master_edit.html', {'purchase': purchase, 'suppliers': suppliers})

def purchase_master_delete(request, id):
    if request.method == "POST":
        purchase = get_object_or_404(PurchaseMaster, id=id)
        purchase.delete()
        messages.success(request, 'Purchase record deleted successfully.')
    return redirect('purchase_master_list')

def purchase_details_list(request):
    purchases = PurchaseDetails.objects.all()
    form = PurchaseDetailsForm()
    return render(request, 'purchase_details_list.html', {'purchases': purchases, 'form': form})

def purchase_details_create(request):
    if request.method == 'POST':
        form = PurchaseDetailsForm(request.POST)
        # purchase_master = get_object_or_404(PurchaseMaster, id=purchase_master_id)

        if form.is_valid():
            purchase = form.save()
            return JsonResponse({'success': True, 'id': purchase.id, 'item_id': purchase.item_id, 'quantity': purchase.quantity, 'price': purchase.price, 'amount': purchase.amount, 'datetime': purchase.datetime.strftime('%Y-%m-%d %H:%M:%S'), 'status': 'Active' if purchase.status else 'Inactive'})
        return JsonResponse({'success': False, 'errors': form.errors})

def purchase_details_edit(request, id):
    purchase = get_object_or_404(PurchaseDetails, id=id)
    if request.method == 'POST':
        form = PurchaseDetailsForm(request.POST, instance=purchase)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'id': purchase.id, 'item_id': purchase.item_id, 'quantity': purchase.quantity, 'price': purchase.price, 'amount': purchase.amount, 'datetime': purchase.datetime.strftime('%Y-%m-%d %H:%M:%S'), 'status': 'Active' if purchase.status else 'Inactive'})
        return JsonResponse({'success': False, 'errors': form.errors})

def purchase_details_delete(request, id):
    purchase = get_object_or_404(PurchaseDetails, id=id)
    purchase.delete()
    return JsonResponse({'success': True, 'id': id})

def brand_list(request):
    brands = BrandMaster.objects.all()
    
    # Handle filtering
    name = request.GET.get('name')
    status = request.GET.get('status')
    
    if name:
        brands = brands.filter(brand_name__icontains=name)
    if status:
        brands = brands.filter(status=status)
    
    # Handle CSV export
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="brands.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Name', 'Status'])
        
        for brand in brands:
            writer.writerow([
                brand.id,
                brand.brand_name,
                'Active' if brand.status else 'Inactive'
            ])
        
        return response
    
    return render(request, 'brand_list.html', {'brands': brands})

def brand_create(request):
    if request.method == "POST":
        brand_name = request.POST.get('brand_name')
        status = request.POST.get('status') == 'True'
        
        if brand_name:
            BrandMaster.objects.create(
                brand_name=brand_name,
                status=status
            )
            messages.success(request, 'Brand added successfully.')
        else:
            messages.error(request, 'Please fill all required fields.')
    return redirect('brand_list')

def brand_edit(request, id):
    brand = get_object_or_404(BrandMaster, id=id)
    if request.method == "POST":
        brand_name = request.POST.get('brand_name')
        status = request.POST.get('status') == 'True'
        
        if brand_name:
            brand.brand_name = brand_name
            brand.status = status
            brand.save()
            messages.success(request, 'Brand updated successfully.')
            return redirect('brand_list')
        else:
            messages.error(request, 'Please fill all required fields.')
    
    return render(request, 'brand_edit.html', {'brand': brand})

def brand_delete(request, id):
    if request.method == "POST":
        try:
            brand = get_object_or_404(BrandMaster, id=id)
            brand.delete()
            messages.success(request, 'Brand deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting brand: {str(e)}')
    return redirect('brand_list')

# List all items
def item_list(request):
    items = Item.objects.all()
    brands = BrandMaster.objects.all()
    
    # Handle filtering
    name = request.GET.get('name')
    brand = request.GET.get('brand')
    status = request.GET.get('status')
    
    if name:
        items = items.filter(item_name__icontains=name)
    if brand:
        items = items.filter(brand_id=brand)
    if status:
        items = items.filter(status=status)
    
    # Handle CSV export
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="items.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Name', 'Brand', 'Status'])
        
        for item in items:
            writer.writerow([
                item.id,
                item.item_name,
                item.brand.brand_name,
                'Active' if item.status else 'Inactive'
            ])
        
        return response
    
    return render(request, 'item_list.html', {'items': items, 'brands': brands})

# Create a new item
@csrf_exempt
def item_create(request):
    if request.method == "POST":
        try:
            item_name = request.POST.get('item_name')
            item_code = request.POST.get('item_code')
            price = request.POST.get('price')
            
            if not item_name or not item_code or not price:
                messages.error(request, 'Please fill all required fields.')
                return redirect('item_list')
            
            Item.objects.create(
                item_name=item_name,
                item_code=item_code,
                price=price
            )
            messages.success(request, 'Item added successfully.')
        except Exception as e:
            messages.error(request, f'Error adding item: {str(e)}')
    return redirect('item_list')

# Edit an item
def item_edit(request, id):
    item = get_object_or_404(Item, id=id)
    brands = BrandMaster.objects.all()
    
    if request.method == "POST":
        item_name = request.POST.get('item_name')
        brand_id = request.POST.get('brand')
        status = request.POST.get('status') == 'True'
        
        if item_name and brand_id:
            brand = get_object_or_404(BrandMaster, id=brand_id)
            item.item_name = item_name
            item.brand = brand
            item.status = status
            item.save()
            messages.success(request, 'Item updated successfully.')
            return redirect('item_list')
        else:
            messages.error(request, 'Please fill all required fields.')
    
    return render(request, 'item_edit.html', {'item': item, 'brands': brands})

# Delete an item
def item_delete(request, id):
    if request.method == "POST":
        try:
            item = get_object_or_404(Item, id=id)
            item.delete()
            messages.success(request, 'Item deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting item: {str(e)}')
    return redirect('item_list')