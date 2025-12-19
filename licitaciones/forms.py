# forms.py
from django import forms
from .models import Licitacion, Financiamiento

class LicitacionForm(forms.ModelForm):
    financiamiento = forms.ModelMultipleChoiceField(
        queryset=Financiamiento.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'size': 5}),
        label="Financiamiento"
    )
    documentos = forms.FileField(
        label="Adjuntar documentos",
        required=False,
        widget=forms.ClearableFileInput(attrs={'multiple': True})
    )

    fecha_creacion = forms.DateField(
        label="Fecha Creación",
        required=False,
        widget=forms.DateInput(attrs={
            'id': 'fechaCreacionInput',  # <--- AQUÍ ESTÁ LA MAGIA
            'class': 'form-control', 
            'type': 'date'
        })
    )

    class Meta:
        model = Licitacion
        fields = [
            # ... resto de campos ...
            'fecha_creacion',
            # ... resto de campos ...
        ]

    class Meta:
        model = Licitacion
        fields = [
            'numero_pedido',
            'fecha_creacion',
            'profesional_a_cargo',
            'id_mercado_publico',
            'numero_cuenta',
            'operador_user',
            'operador_2',
            'iniciativa',
            'direccion',
            'institucion',
            'moneda',
            'categoria',
            'financiamiento',
            'monto_presupuestado',
            'tipo_presupuesto',
            'en_plan_anual',
            'etapa_fk',
            'departamento',
            'llamado_cotizacion',
            'pedido_devuelto',
            'tipo_licitacion',
            'licitacion_fallida_linkeada'
        ]
        widgets = {
            'tipo_licitacion': forms.HiddenInput(),
            'licitacion_fallida_linkeada': forms.HiddenInput(),
            'profesional_a_cargo': forms.TextInput(attrs={'class': 'form-control', 'id': 'profesionalCargoInput'}),
        }
