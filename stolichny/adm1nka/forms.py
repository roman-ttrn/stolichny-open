from django import forms
from store.models import Product, Category

class ProductForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'price', 'categories', 'image',
            'protein', 'fat', 'carbs', 'kkal', 'weight', 'weight_dependence'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Название продукта'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Описание продукта',
                'rows': 4
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Цена',
                'step': '0.01',
                'min': '0'
            }),
            'image': forms.ClearableFileInput(attrs={'class': 'form-file'}),
            
            'protein': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Белки (г)',
                'min': '0'
            }),
            'fat': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Жиры (г)',
                'min': '0'
            }),
            'carbs': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Углеводы (г)',
                'min': '0'
            }),
            'kkal': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Калории (ккал)',
                'min': '0'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Вес (г)',
                'min': '0'
            }),
            'weight_dependence': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
        }
    
    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price <= 0:
            raise forms.ValidationError("Цена должна быть положительным числом")
        return price
    
    def clean_protein(self):
        protein = self.cleaned_data.get('protein')
        if protein is not None and protein < 0:
            raise forms.ValidationError("Белки не могут быть отрицательными")
        return protein
    
    def clean_fat(self):
        fat = self.cleaned_data.get('fat')
        if fat is not None and fat < 0:
            raise forms.ValidationError("Жиры не могут быть отрицательными")
        return fat
    
    def clean_carbs(self):
        carbs = self.cleaned_data.get('carbs')
        if carbs is not None and carbs < 0:
            raise forms.ValidationError("Углеводы не могут быть отрицательными")
        return carbs
    
    def clean_kkal(self):
        kkal = self.cleaned_data.get('kkal')
        if kkal is not None and kkal < 0:
            raise forms.ValidationError("Калории не могут быть отрицательными")
        return kkal
    
    def clean_weight(self):
        weight = self.cleaned_data.get('weight')
        if weight is not None and weight <= 0:
            raise forms.ValidationError("Вес должен быть положительным числом")
        return weight