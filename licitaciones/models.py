from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone


class Etapa(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class Estado(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre

class TipoLicitacion(models.Model):
    nombre = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.nombre

class Moneda(models.Model):
    nombre = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.nombre
    
class Categoria(models.Model):
    nombre = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.nombre
    
class Financiamiento(models.Model):
    nombre = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.nombre

class Departamento(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

class Licitacion(models.Model):
    class Meta:
        db_table = 'licitacion_licitacion'
    
    LLAMADO_COTIZACION_CHOICES = [
        ('primer_llamado', 'Primer llamado'),
        ('segundo_llamado', 'Segundo llamado'),
        ('tercer_llamado', 'Tercer llamado'),
        ('cuarto_llamado', 'Cuarto llamado'),
        ('quinto_llamado', 'Quinto llamado'),
    ]

    TIPO_PRESUPUESTO_CHOICES = [
        ('le', 'LE'),
        ('lp', 'LP'),
        ('lr', 'LR'),
    ]
    
    id = models.AutoField(primary_key=True)  
    operador_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='licitaciones_asignadas', verbose_name="Operador 1")
    operador_2 = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='licitaciones_operador_2', verbose_name="Operador 2")
    etapa_fk = models.ForeignKey('Etapa', on_delete=models.SET_NULL, null=True, blank=True, related_name='proyectos_etapa')
    estado_fk = models.ForeignKey('Estado', on_delete=models.SET_NULL, null=True, blank=True, related_name='proyectos_estado')
    tipo_licitacion = models.ForeignKey('TipoLicitacion', on_delete=models.PROTECT, related_name='licitaciones')
    moneda = models.ForeignKey('Moneda', on_delete=models.PROTECT, related_name='licitaciones', null=True, blank=True)
    numero_pedido = models.IntegerField(verbose_name="N° de pedido")
    id_mercado_publico = models.CharField(max_length=50, blank=True, null=True, verbose_name="ID Mercado Público")
    categoria = models.ForeignKey('Categoria', on_delete=models.PROTECT, related_name='licitaciones', null=True, blank=True)
    financiamiento = models.ManyToManyField('Financiamiento', related_name='licitaciones', blank=True)
    numero_cuenta = models.CharField(max_length=30, verbose_name="N° de cuenta")
    en_plan_anual = models.BooleanField(default=False, verbose_name="¿Está en el plan anual?")
    justificacion_plan = models.TextField(blank=True, null=True, verbose_name="Justificación Plan Anual")
    iniciativa = models.CharField(max_length=255, blank=True, null=True)
    departamento = models.ForeignKey('Departamento', on_delete=models.SET_NULL, null=True, blank=True, related_name='licitaciones')
    monto_presupuestado = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Monto Presupuestado")
    llamado_cotizacion = models.CharField(
        max_length=20, 
        choices=LLAMADO_COTIZACION_CHOICES,
        blank=True, 
        null=True, 
        verbose_name="Llamado Cotización"
    )
    tipo_presupuesto = models.CharField(
        max_length=2,
        choices=TIPO_PRESUPUESTO_CHOICES,
        default='le',
        verbose_name="Tipo por presupuesto",
        null=True,
    )
    fecha_creacion = models.DateTimeField(
        default=timezone.now, 
        verbose_name="Fecha de Asignación / Creación"
    )
    fecha_tentativa_termino = models.DateField(blank=True, null=True, verbose_name="Fecha tentativa de término")
    licitacion_fallida_linkeada = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='nuevas_licitaciones', verbose_name="Licitación fallida linkeada")
    direccion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dirección")
    institucion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Institución")
    pedido_devuelto = models.BooleanField(default=False, verbose_name="Pedido devuelto")

    empresa_adjudicacion = models.CharField(max_length=100, blank=True, null=True, verbose_name="Empresa de adjudicación")
    rut_adjudicacion = models.CharField(max_length=20, blank=True, null=True, verbose_name="Rut de empresa de adjudicación")
    monto_adjudicacion = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, verbose_name="Fecha de decreto de adjudicación")
    fecha_decreto_adjudicacion = models.DateField(blank=True, null=True)
    fecha_subida_mercado_publico_adjudicacion = models.DateField(blank=True, null=True, verbose_name="Fecha de subida de adjudicación a mercado público")
    orden_compra_adjudicacion = models.CharField(
    max_length=50,
    blank=True,
    null=True,
    verbose_name="Orden de compra de adjudicación"
)

    fecha_evaluacion_tecnica_evaluacion = models.DateField(blank=True, null=True, verbose_name="Fecha que se envía evaluación técnica")
    nombre_integrante_uno_evaluacion = models.CharField(max_length=100, blank=True, null=True, verbose_name="Integrante uno evaluación")
    nombre_integrante_dos_evaluacion = models.CharField(max_length=100, blank=True, null=True, verbose_name="Integrante dos evaluación")
    nombre_integrante_tres_evaluacion = models.CharField(max_length=100, blank=True, null=True, verbose_name="Integrante tres evaluación")
    fecha_comision_evaluacion = models.DateField(blank=True, null=True, verbose_name="Fecha de comisión")

    fecha_cierre_preguntas_publicacionportal = models.DateField(blank=True, null=True, verbose_name="Fecha de cierre de preguntas")
    fecha_respuesta_publicacionportal = models.DateField(blank=True, null=True, verbose_name="Fecha de respuesta")
    fecha_visita_terreno_publicacionportal = models.DateField(blank=True, null=True, verbose_name="Fecha de visita a terreno")
    fecha_cierre_oferta_publicacionportal = models.DateField(blank=True, null=True, verbose_name="Fecha de cierre de oferta")
    fecha_apertura_tecnica_publicacionportal = models.DateField(blank=True, null=True, verbose_name="Fecha de apertura técnica")
    fecha_apertura_economica_publicacionportal = models.DateField(blank=True, null=True, verbose_name="Fecha de apertura económica")
    fecha_estimada_adjudicacion_publicacionportal = models.DateField(blank=True, null=True, verbose_name="Fecha estimada de adjudicación")

    fecha_disponibilidad_presupuestaria = models.DateField(blank=True, null=True, verbose_name="Fecha que se pide disponibilidad presupuestaria")

    fecha_solicitud_regimen_interno = models.DateField(blank=True, null=True, verbose_name="Fecha de solicitud de régimen interno")
    fecha_recepcion_documento_regimen_interno = models.DateField(blank=True, null=True, verbose_name="Fecha de llegada de documento")

    fecha_tope_firma_contrato = models.DateField(blank=True, null=True, verbose_name="Fecha tope de firma de contrato")

    fecha_evaluacion_cotizacion = models.DateField(blank=True, null=True, verbose_name="Fecha de evaluacion de la cotizacion")
    monto_estimado_cotizacion = models.DecimalField(blank=True, null=True, max_digits=15, decimal_places=2, verbose_name="Monto estimado de cotización")

    fecha_solicitud_intencion_compra = models.DateField(blank=True, null=True, verbose_name="Fecha de la solicitud de intencion de compra")

    nombre_integrante_uno_comision_base = models.CharField(max_length=100, blank=True, null=True, verbose_name="Integrante uno de la comisión")
    nombre_integrante_dos_comision_base = models.CharField(max_length=100, blank=True, null=True, verbose_name="Integrante dos de la comisión")
    nombre_integrante_tres_comision_base = models.CharField(max_length=100, blank=True, null=True, verbose_name="Integrante tres de la comisión")

    fecha_publicacion_mercado_publico = models.DateField(blank=True, null=True, verbose_name="Fecha de publicación en mercado público")
    fecha_cierre_ofertas_mercado_publico = models.DateField(blank=True, null=True, verbose_name="Fecha de cierre de ofertas en mercado público")
    profesional_a_cargo = models.CharField(max_length=100, null=True, blank=True)
    # Tipos de licitación fallida (cuando fallida es True)
    TIPO_FALLIDA_CHOICES = [
        ('revocada', 'Revocada'),
        ('anulada', 'Anulada'),
        ('desierta', 'Desierta'),
    ]
    tipo_fallida = models.CharField(
        max_length=10, 
        choices=TIPO_FALLIDA_CHOICES,
        blank=True, 
        null=True, 
        verbose_name="Tipo de Licitación Fallida"
    )

    def __str__(self):
        return self.iniciativa


   # ACA ES PARA EL TEMA DE LAS ETAPAS EN OPERADORES
    def get_operador_activo(self):
        """
        Retorna el operador activo según la etapa actual.
        - Operador 1: Hasta la etapa 'Evaluación de Ofertas' (inclusive)
        - Operador 2: Desde la etapa posterior a 'Evaluación de Ofertas'
        Esta versión es robusta ante etapas saltadas y compara por el campo 'orden'.
        """
        if not self.etapa_fk:
            return self.operador_user

        # Obtener todas las relaciones etapa-tipo ordenadas
        etapas_tipo = self.tipo_licitacion.etapas_rel.order_by('orden').all()
        # Buscar la relación de la etapa actual
        rel_actual = None
        orden_actual = None
        for rel in etapas_tipo:
            if rel.etapa_id == self.etapa_fk.id:
                rel_actual = rel
                orden_actual = rel.orden
                break
        if orden_actual is None:
            # Si la etapa actual no está en la lista, operador 1 por defecto
            return self.operador_user

        # Buscar el menor 'orden' de una etapa que contenga 'evaluación de ofertas'
        orden_evaluacion = None
        for rel in etapas_tipo:
            if 'evaluación de ofertas' in rel.etapa.nombre.lower() or 'evaluación de la cotizacion' in rel.etapa.nombre.lower():
                if orden_evaluacion is None or rel.orden < orden_evaluacion:
                    orden_evaluacion = rel.orden

        if orden_evaluacion is None:
            # Si no se encontró la etapa de evaluación de ofertas, operador 1 por defecto
            return self.operador_user

        # Si estamos en o antes de "Evaluación de Ofertas", operador 1
        # Si estamos después, operador 2
        if orden_actual <= orden_evaluacion:
            return self.operador_user
        else:
            return self.operador_2 if self.operador_2 else self.operador_user

    def get_numero_operador_activo(self):
        """
        Retorna 1 o 2 según qué operador está activo actualmente
        """
        operador_activo = self.get_operador_activo()
        if operador_activo == self.operador_2:
            return 2
        return 1

    def puede_operar_usuario(self, usuario):
        """
        Determina si un usuario puede operar en esta licitación según la etapa actual
        """
        if not usuario:
            return False
        
        # Los admin pueden operar siempre
        if hasattr(usuario, 'perfil') and usuario.perfil.rol == 'admin':
            return True
        
        # Verificar si es el operador activo
        operador_activo = self.get_operador_activo()
        return operador_activo == usuario

    def get_saltar_etapas(self):
        """
        Determina si esta licitación debe saltar las etapas 'Solicitud de comisión de régimen interno', 'Recepción de documento de régimen interno' y 'Aprobación del consejo'
        cuando el monto es menor a 500 utm
        """
        saltar_etapas = []
        
        monedas = {'uf': 39156.08, 'dolar': 965.64, 'dólar': 965.64, 'usd': 965.64, 'euro': 1125.59, 'eur': 1125.59, 'utm': 68647, 'clp': 1}
        # saltar etapas solicitud de comision de regimen interno, recepcion de documento de regimen interno y aprobacion del concejo municipal segun monto presupuestado
        try:
            if monedas[self.moneda.nombre.lower()]*float(self.monto_presupuestado) < 500 * monedas['utm']:
                saltar_etapas.append((11, 11))
                saltar_etapas.append((14, 16))
            return saltar_etapas
        except (ValueError, TypeError):
            # Si no se puede convertir a número, no saltar la aprobación
            return saltar_etapas
        return saltar_etapas

    def get_etapas_habilitadas(self):
        """
        Retorna las etapas habilitadas para esta licitación,
        excluyendo las etapas saltadas si aplica
        """
        # Obtener todas las etapas del tipo de licitación a través de la tabla intermedia
        etapas_tipo = list(self.tipo_licitacion.etapas_rel.order_by('orden').all())
        saltar_etapas = self.get_saltar_etapas()
        for e_inicio, e_fin in saltar_etapas:
            etapas_tipo = [
                rel for rel in etapas_tipo 
                if rel.etapa.id not in range(e_inicio, e_fin + 1)
            ]
        return etapas_tipo
    
    def get_etapas_todas_con_inhabilitacion(self):
        """
        Retorna todas las etapas del tipo de licitación con información de si están inhabilitadas
        """
        # Obtener todas las etapas del tipo de licitación a través de la tabla intermedia
        etapas_tipo = list(self.tipo_licitacion.etapas_rel.order_by('orden').all())
        saltar_etapas = self.get_saltar_etapas()
        
        etapas_con_info = []
        for rel in etapas_tipo:
            etapa_info = {
                'rel': rel,
                'etapa': rel.etapa,
                'inhabilitada': False
            }
            
            for e_inicio, e_fin in saltar_etapas:
                if rel.etapa.id in range(e_inicio, e_fin + 1):
                    etapa_info['inhabilitada'] = True
                
            etapas_con_info.append(etapa_info)
        
        return etapas_con_info


class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ROL_CHOICES = (
        ('admin', 'Administrador'),
        ('operador', 'Operador'),
        ('vizualizador', 'Vizualizador'),
    )
    rol = models.CharField(max_length=20, choices=ROL_CHOICES)

    def __str__(self):
        return f"{self.user.username} ({self.rol})"

class BitacoraLicitacion(models.Model):
    licitacion = models.ForeignKey(Licitacion, on_delete=models.CASCADE, related_name='bitacoras')
    # Removed operador field - now using operador_user (User model)
    operador_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='bitacoras_operador')
    texto = models.TextField(verbose_name="Comentario/Acción")
    fecha = models.DateTimeField(auto_now_add=True)
    etapa = models.ForeignKey(Etapa, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.licitacion} - {self.operador_user} - {self.fecha:%d/%m/%Y %H:%M}"

class DocumentoLicitacion(models.Model):
    licitacion = models.ForeignKey(Licitacion, on_delete=models.CASCADE, related_name='documentos')
    archivo = models.FileField(upload_to='documentos_licitacion/')
    nombre = models.CharField(max_length=255, blank=True, null=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre or self.archivo.name

@receiver(post_delete, sender=DocumentoLicitacion)
def eliminar_archivo_documento(sender, instance, **kwargs):
    if instance.archivo:
        instance.archivo.delete(False)

class TipoLicitacionEtapa(models.Model):
    tipo_licitacion = models.ForeignKey(TipoLicitacion, on_delete=models.CASCADE, related_name='etapas_rel')
    etapa = models.ForeignKey(Etapa, on_delete=models.CASCADE, related_name='tipos_licitacion_rel')
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('tipo_licitacion', 'etapa')
        ordering = ['tipo_licitacion', 'orden']

    def __str__(self):
        return f"{self.tipo_licitacion} - {self.etapa} (Orden: {self.orden})"

class ObservacionBitacora(models.Model):
    bitacora = models.OneToOneField(BitacoraLicitacion, on_delete=models.CASCADE, related_name='observacion')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='bitacoras_usuario')
    texto = models.TextField(verbose_name="Observación")
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Obs. {self.bitacora_id}: {self.texto[:40]}..."
    
class DocumentoObservacion(models.Model):
    bitacora = models.ForeignKey(ObservacionBitacora, on_delete=models.CASCADE, related_name='archivos')
    archivo = models.FileField(upload_to='documentos_licitacion/')
    nombre = models.CharField(max_length=255, blank=True, null=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre or self.archivo.name

class DocumentoBitacora(models.Model):
    bitacora = models.ForeignKey(BitacoraLicitacion, on_delete=models.CASCADE, related_name='archivos')
    archivo = models.FileField(upload_to='documentos_licitacion/')
    nombre = models.CharField(max_length=255, blank=True, null=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre or self.archivo.name

class Notificacion(models.Model):
    TIPO_CHOICES = [
        ('observacion', 'Nueva Observación'),
        ('etapa', 'Cambio de Etapa'),
        ('cerrada', 'Licitación Cerrada'),
        ('documento', 'Documento Subido'),
        ('general', 'General'),
    ]
    
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='general')
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    licitacion = models.ForeignKey(Licitacion, on_delete=models.CASCADE, related_name='notificaciones', null=True, blank=True)
    operador_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='notificaciones_operador')
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='notificaciones_admin')
    fecha = models.DateTimeField(auto_now_add=True)
    leida = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.titulo} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"