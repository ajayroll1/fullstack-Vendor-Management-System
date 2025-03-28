from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import Supplier, SalesMaster, PurchaseMaster, Item, PurchaseDetails, BrandMaster, SalesDetails
from .forms import SupplierForm, SalesMasterForm, PurchaseMasterForm, ItemForm, PurchaseDetailsForm, BrandMasterForm
from datetime import date, datetime
from django.db.models import Max
import csv
from django.db.models import Sum

def report(request):
    # Get all counts for the statistics cards
    total_items = Item.objects.count()
    total_suppliers = Supplier.objects.count()
    
    # Calculate total sales amount
    total_sales_amount = SalesMaster.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Calculate total purchase amount
    total_purchase_amount = PurchaseMaster.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Calculate total stock (total purchase quantities)
    total_stock = PurchaseDetails.objects.aggregate(total=Sum('quantity'))['total'] or 0
    
    # Get report type and filters
    report_type = request.GET.get('report_type')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status = request.GET.get('status')
    
    # Initialize variables
    sales = []
    sales_total = 0
    purchases = []
    purchases_total = 0
    items = []
    total_stock_value = 0
    
    # Generate reports based on type
    if report_type == 'sales':
        # Get sales data with filters
        sales_query = SalesMaster.objects.all()
        
        if start_date:
            sales_query = sales_query.filter(invoice_date__gte=start_date)
        if end_date:
            sales_query = sales_query.filter(invoice_date__lte=end_date)
            
        sales = sales_query.order_by('-invoice_date')
        sales_total = sales.aggregate(total=Sum('total_amount'))['total'] or 0
        
    elif report_type == 'purchases':
        # Get purchase data with filters
        purchases_query = PurchaseMaster.objects.all()
        
        if start_date:
            purchases_query = purchases_query.filter(invoice_date__gte=start_date)
        if end_date:
            purchases_query = purchases_query.filter(invoice_date__lte=end_date)
        if status and status in ['True', 'False']:
            purchases_query = purchases_query.filter(status=(status == 'True'))
            
        purchases = purchases_query.order_by('-invoice_date')
        purchases_total = purchases.aggregate(total=Sum('total_amount'))['total'] or 0
        
    elif report_type == 'stock':
        # Get items data
        items_query = Item.objects.all()
        
        if status and hasattr(Item, 'status'):
            items_query = items_query.filter(status=status)
            
        items = items_query
        
        # Calculate stock value for each item
        for item in items:
            if hasattr(item, 'stock'):
                item.stock_value = item.stock * item.price
                total_stock_value += item.stock_value
            else:
                item.stock_value = 0

    return render(request, 'report.html', {
        'total_items': total_items,
        'total_suppliers': total_suppliers,
        'total_sales': total_sales_amount,
        'total_purchases': total_purchase_amount,
        'total_stock': total_stock,
        'sales': sales,
        'sales_total': sales_total,
        'purchases': purchases,
        'purchases_total': purchases_total,
        'items': items,
        'total_stock_value': total_stock_value
    })

def index(request):
    # Get counts for dashboard stats
    total_items = Item.objects.filter(status=True).count() if hasattr(Item, 'status') else Item.objects.count()
    total_suppliers = Supplier.objects.filter(status=True).count()
    
    # Get total sales and purchases amount
    total_sales_amount = SalesMaster.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    total_purchases_amount = PurchaseMaster.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Get recent sales (last 5)
    recent_sales = SalesMaster.objects.all().order_by('-invoice_date')[:5]
    
    # Get recent purchases (last 5)
    recent_purchases = PurchaseMaster.objects.all().order_by('-invoice_date')[:5]
    
    # Get low stock items (items with stock less than 5)
    # Assuming 'stock' field exists in Item model, otherwise comment this line
    low_stock_items = []
    if hasattr(Item, 'stock'):
        low_stock_items = Item.objects.filter(stock__lt=5)
        if hasattr(Item, 'status'):
            low_stock_items = low_stock_items.filter(status=True)
    
    context = {
        'total_items': total_items,
        'total_suppliers': total_suppliers,
        'total_sales': f"${total_sales_amount:,.2f}",
        'total_purchases': f"${total_purchases_amount:,.2f}",
        'recent_sales': recent_sales,
        'recent_purchases': recent_purchases,
        'low_stock_items': low_stock_items,
    }
    
    return render(request, 'index.html', context)

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
        try:
            # Generate invoice number using existing function
            invoice_no = generate_invoice_number('SALE')
            
            # Get form data
            invoice_date = request.POST.get('invoice_date')
            total_amount = request.POST.get('total_amount')
            customer_name = request.POST.get('customer_name')
            number = request.POST.get('number')
            item_id = request.POST.get('item')
            
            if not all([invoice_date, total_amount, customer_name, item_id]):
                messages.error(request, 'Please fill all required fields')
                return redirect('sales_master_list')  # Redirect back to list page instead
            
            # Get the selected item
            item = get_object_or_404(Item, id=item_id)
            
            # Create SalesMaster record
            sales_master = SalesMaster.objects.create(
                invoice_no=invoice_no,
                invoice_date=invoice_date,
                total_amount=float(total_amount),
                customer_name=customer_name,
                number=number if number else "",  # Make number optional
                item=item
            )
            
            # Process individual items
            items = request.POST.getlist('items[]')
            quantities = request.POST.getlist('quantities[]')
            prices = request.POST.getlist('prices[]')
            amounts = request.POST.getlist('amounts[]')
            
            # Create SalesDetails records for multiple items
            for i in range(len(items)):
                if items[i]:  # Only create if item is selected
                    detail_item = get_object_or_404(Item, id=items[i])
                    SalesDetails.objects.create(
                        item=detail_item,
                        quantity=quantities[i],
                        price=prices[i],
                        amount=amounts[i],
                        sales_master=sales_master
                    )
            
            messages.success(request, 'Sales record created successfully!')
            return redirect('sales_master_list')  # Always redirect to the list page
        except Exception as e:
            messages.error(request, f'Error creating sales record: {str(e)}')
            return redirect('sales_master_list')  # Redirect back to list page on error
    
    # This part won't be reached from the "Save Sale" button on the list page,
    # but keeps compatibility with any direct access to this URL
    items = Item.objects.all()
    return render(request, 'sales_master_create.html', {'items': items})

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
            
            # Get form data
            supplier_id = request.POST.get('supplier')
            total_amount = request.POST.get('total_amount')
            item_id = request.POST.get('item') if 'item' in request.POST else None
            invoice_date = request.POST.get('invoice_date') or today
            
            if supplier_id and total_amount:
                supplier = get_object_or_404(Supplier, id=supplier_id)
                # Get a default item if none specified
                item = get_object_or_404(Item, id=item_id) if item_id else Item.objects.first()
                
                # Create PurchaseMaster record
                purchase_master = PurchaseMaster.objects.create(
                    invoice_no=invoice_no,
                    invoice_date=invoice_date,
                    supplier=supplier,
                    total_amount=float(total_amount),
                    item=item
                )
                
                # Handle purchase details
                items = request.POST.getlist('items[]')
                quantities = request.POST.getlist('quantities[]')
                prices = request.POST.getlist('prices[]')
                amounts = request.POST.getlist('amounts[]')
                
                # Create purchase details records
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
    try:
        item = get_object_or_404(Item, id=id)
        item.delete()
        messages.success(request, 'Item deleted successfully.')
    except Exception as e:
        messages.error(request, f'Error deleting item: {str(e)}')
    return redirect('item_list')