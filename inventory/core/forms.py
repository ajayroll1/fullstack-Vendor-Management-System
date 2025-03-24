from django import forms
from .models import Supplier
from .models import SalesMaster
from .models import PurchaseMaster
from .models import PurchaseDetails
from .models import Item
from .models import BrandMaster




class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['supplier_name', 'mobile_no', 'address', 'status']

class SalesMasterForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SalesMasterForm, self).__init__(*args, **kwargs)

        # Define ModelChoiceField before looping over visible fields
        self.fields['item'] = forms.ModelChoiceField(
            queryset=Item.objects.all(),
            widget=forms.Select(attrs={'onchange': 'updatePrice()'})
        )

        # Apply 'form-control' class to all fields
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

    class Meta:
        model = SalesMaster
        fields = ['customer_name', 'number', 'total_amount', 'item', 'quantity', 'price']
        widgets = {
            'price': forms.NumberInput(attrs={'step': '0.01'}),
            'quantity': forms.NumberInput(attrs={'min': '1'}),
        }
class PurchaseMasterForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(PurchaseMasterForm, self).__init__(*args, **kwargs)

        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
            
            self.fields['supplier']=forms.ModelChoiceField(queryset=Supplier.objects.filter(status=1))
            self.fields['item']=forms.ModelChoiceField(queryset=Item.objects.all(),  widget=forms.Select(attrs={'onchange': 'updatePrice()'}))

    class Meta:
        model = PurchaseMaster
        fields = [ 'supplier', 'total_amount', 'status','item']
        widgets = {
            'invoice_date': forms.DateInput(attrs={'type': 'date'}),
            'status': forms.Select(choices=[(True, 'Active'), (False, 'Inactive')]),
        }


class PurchaseDetailsForm(forms.ModelForm):
    class Meta:
        model = PurchaseDetails
        fields = ['item', 'quantity', 'price', 'amount', 'purchase_master', 'status']
        # widgets = {
        #     'amount': forms.TextInput(attrs={'readonly': 'readonly'}),  # Readonly field
        # }

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity <= 0:
            raise forms.ValidationError("Quantity must be greater than zero.")
        return quantity

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price <= 0:
            raise forms.ValidationError("Price must be greater than zero.")
        return price



class ItemForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ItemForm, self).__init__(*args, **kwargs)

        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

    class Meta:
        model = Item
        fields = ['item_name', 'item_code', 'price']



class BrandMasterForm(forms.ModelForm):
    class Meta:
        model = BrandMaster
        fields = ['brand_name']