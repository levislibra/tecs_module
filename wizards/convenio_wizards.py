# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import datetime, timedelta
from dateutil import relativedelta
from openerp.exceptions import UserError, ValidationError
import time
import math

class ConvenioWizards(models.TransientModel):
	_name = 'convenio.wizard'

	dia = fields.Char('Dia')
	mes = fields.Char('Mes')
	ano = fields.Char('Año')
	nombre = fields.Char('Cliente')
	dni = fields.Char('DNI')
	ocupacion = fields.Char('Ocupacion')
	calle = fields.Char('Calle')
	numero = fields.Char('Numero')
	entre_calles = fields.Char('Entre calles')
	partido = fields.Char('Partido')
	localidad = fields.Char('Localidad')
	direccion2 = fields.Char('Direccion 2')
	cel = fields.Char('Cel')
	tel2 = fields.Char('Tel 2')
	facebook = fields.Char('Facebook')
	email = fields.Char('Email')
	forma_pago = fields.Selection([
		('domicilio', 'Domicilio'),
		('electronico', 'Pago electronico')
		], 'Forma de pago')
	articulo = fields.Char('Articulo')
	marca = fields.Char('Marca')
	suma_inicial = fields.Char('Suma inicial')
	plazo = fields.Char('Plazo no mayor a')
	forma_de_cuotas = fields.Char('Forma de cuota')
	cantidad_cuotas = fields.Char('Cantidad de cuotas')
	monto_cuotas = fields.Char('Monto de cuotas')

	