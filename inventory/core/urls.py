from django.urls import path
from .views import supplier_list, supplier_create, supplier_edit, supplier_delete
from .views import sales_master_list, sales_master_create, sales_master_edit, sales_master_delete
from .views import purchase_master_list, purchase_master_create, purchase_master_edit, purchase_master_delete
from .views import purchase_details_list, purchase_details_create, purchase_details_edit, purchase_details_delete
from .views import brand_list, brand_create, brand_edit, brand_delete
from .views import item_list, item_create, item_edit, item_delete
from .views import index, report

urlpatterns = [
    path('', index, name='index'),
    path("report/", report, name="report"),
    
    # Supplier URLs
    path('supplier_list', supplier_list, name='supplier_list'),
    path('create/', supplier_create, name='supplier_create'),
    path('edit/<int:id>/', supplier_edit, name='supplier_edit'),
    path('supplier/delete/<int:id>/', supplier_delete, name='supplier_delete'),
    
    # Sales URLs
    path('sales/', sales_master_list, name='sales_master_list'),
    path('sales/create/', sales_master_create, name='sales_master_create'),
    path('sales/edit/<int:id>/', sales_master_edit, name='sales_master_edit'),
    path('sales/delete/<int:id>/', sales_master_delete, name='sales_master_delete'),
    
    # Purchase Master URLs
    path('purchase-master/', purchase_master_list, name='purchase_master_list'),
    path('purchase-master/create/', purchase_master_create, name='purchase_master_create'),
    path('purchase-master/edit/<int:pk>/', purchase_master_edit, name='purchase_master_edit'),
    path('purchase-master/delete/<int:pk>/', purchase_master_delete, name='purchase_master_delete'),
    
    # Purchase Details URLs
    path('purchase-details/', purchase_details_list, name='purchase_details_list'),
    path('purchase-details/create/', purchase_details_create, name='purchase_details_create'),
    path('purchase-details/edit/<int:id>/', purchase_details_edit, name='purchase_details_edit'),
    path('purchase-details/delete/<int:id>/', purchase_details_delete, name='purchase_details_delete'),
    
    # Brand URLs
    path('brands/brands', brand_list, name='brand_list'),
    path('brands/create/', brand_create, name='brand_create'),
    path('brands/edit/<int:id>/', brand_edit, name='brand_edit'),
    path('brands/delete/<int:id>/', brand_delete, name='brand_delete'),
    
    # Item URLs
    path('item_list/', item_list, name='item_list'),
    path('item_create/', item_create, name='item_create'),
    path('item_edit/<int:id>/', item_edit, name='item_edit'),
    path('item_delete/<int:id>/', item_delete, name='item_delete'),
]







    


