# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import UserError
from openerp.exceptions import ValidationError
from datetime import datetime, timedelta
import amount_to_text_es_MX

class ExtendsInvoice(models.Model):
	_name = 'account.invoice'
	_inherit = 'account.invoice'

	periodo = fields.Selection([('semanal', 'Semanal'), ('quincenal', 'Quincenal'), ('mensual', 'Mensual')], string='Periodo', select=True, default='semanal')
	cuotas = fields.Integer('Cuotas')
	monto_cuota = fields.Float('Monto cuota')
	producto_id = fields.Many2one('product.product', 'Producto')
	precio_sugerido = fields.Float('Precio sugerido', compute='_compute_precio_sugerido')
	descripcion = fields.Char('Descripcion')
	cuota_ids = fields.One2many('account.move.line', 'factura_id', 'Cuotas', compute='_compute_cuota_ids')
	#payment_term_id = fields.Many2one('account.payment.term', 'Plazo de pago', compute='computar_plazo')
	invoice_line_id = fields.Many2one('account.invoice.line', 'Linea de factura')

	@api.one
	@api.onchange('producto_id')
	def _compute_precio_sugerido(self):
		if len(self.producto_id) > 0:
			self.precio_sugerido = self.producto_id.lst_price


	@api.one
	def _compute_cuota_ids(self):
		cr = self.env.cr
		uid = self.env.uid
		cuota_obj = self.pool.get('account.move.line')
		cuota_ids = cuota_obj.search(cr, uid, [
			('invoice_id', '=', self.id),
			('debit', '>', 0),
			])
		self.cuota_ids = cuota_ids

	@api.multi
	def amount_to_text(self):
		return amount_to_text_es_MX.get_amount_to_text(self, self.monto_cuota, 'centavos', 'pesos con ')

	@api.one
	def actualizar(self):
		if len(self.producto_id) > 0:
			if self.descripcion and len(self.descripcion) > 0:
				descripcion = self.descripcion
			else:
				descripcion = self.producto_id.name

			if len(self.invoice_line_id) == 0:
				"""
				ail = self.env['account.invoice.line'].create({
					'product_id': self.producto_id.id,
					'name': descripcion,
					'quantity': 1,
					'price_unit': self.cuotas * self.monto_cuota,
					'account_id': self.journal_id.default_debit_account_id.id,
					#'invoice_id': self.id,
				})
				#self.invoice_line_id = ail.id
				#self.invoice_line_ids = [ail.id]
				"""
				ail = {
					'product_id': self.producto_id.id,
					'name': descripcion,
					'quantity': 1,
					'price_unit': self.cuotas * self.monto_cuota,
					'account_id': self.journal_id.default_debit_account_id.id,
					'invoice_id': self.id,
				}
				self.invoice_line_ids = [(0,0,ail)]
				self.invoice_line_id = self.invoice_line_ids[0].id
			else:
				self.invoice_line_id.product_id = self.producto_id.id
				self.invoice_line_id.name = descripcion
				self.invoice_line_id.price_unit = self.cuotas * self.monto_cuota
				self.invoice_line_id.account_id = self.journal_id.default_debit_account_id.id

	def dias_periodo(self):
		ret = 0
		if self.periodo == 'semanal':
			ret = 7
		elif self.periodo == 'quincenal':
			ret = 14
		elif self.periodo == 'mensual':
			ret = 30
		else:
			raise ValidationError("El periodo no esta definido.")
		return ret

	def delete_payment_term_line(self):
		for apt in self.payment_term_id.line_ids:
			apt.unlink()

	def create_payment_term_line(self):
		# i = 0 ya que la primer cuota es en el momento.
		i = 0
		ptl_ids = []
		while i < self.cuotas:
			if i != (self.cuotas-1):
				ptl = {
					'option': 'day_after_invoice_date',
					'value': 'fixed',
					'value_amount': self.monto_cuota,
					'days': self.dias_periodo() * i,
					'payment_id': self.payment_term_id.id,
				}
			else:
				ptl = {
					'option': 'day_after_invoice_date',
					'value': 'balance',
					'value_amount': self.monto_cuota,
					'days': self.dias_periodo() * i,
					'payment_id': self.payment_term_id.id,
				}
			ptl_ids.append((0,0,ptl))
			i += 1
		self.payment_term_id.line_ids = ptl_ids

	@api.one
	def computar_plazo(self):
		name = str(self.cuotas) + " cuotas " + str(self.periodo)
		if len(self.payment_term_id) == 0:
			#Creamos el termino de pago
			company_id = self.env['res.users'].browse(self.env.uid).company_id.id
			pti = self.env['account.payment.term'].create({
					'name': name,
					'company_id': company_id,
					'active': True,
				})
			self.payment_term_id = pti.id
			self.delete_payment_term_line()
			self.create_payment_term_line()
		else:
			#Actualizamos el termino de pago
			self.payment_term_id.name = name
			self.delete_payment_term_line()
			self.create_payment_term_line()

	@api.onchange('periodo', 'cuotas', 'monto_cuota', 'producto_id', 'descripcion')
	def onchange_values(self):
		self.actualizar()

	@api.one
	@api.constrains('state')
	def _check_values(self):
		if self.state == 'open' and self.type == 'out_invoice':
			if self.cuotas != len(self.payment_term_id.line_ids):
				raise UserError("Debe Computar plazo, ya que la cantidad de cuotas no coinciden.")
			if self.monto_cuota != self.payment_term_id.line_ids[0].value_amount:
				raise UserError("Debe Computar plazo, ya que el monto de cuota no coincide.")
			if len(self.payment_term_id.line_ids) <= 1:
				raise UserError("La cantidad de cuotas debe ser mayor a una.")
			if self.dias_periodo() != self.payment_term_id.line_ids[1].days:
				raise UserError("Debe Computar plazo, ya que el periodo de las cuotas no coinciden.")

class AccountMoveLine(models.Model):
	_name = 'account.move.line'
	_inherit = 'account.move.line'

	_order = 'date_maturity asc'
	factura_id = fields.Many2one('account.invoice', 'Factura')
	producto_id = fields.Many2one('product.product', 'Producto', compute='_compute_producto')

	@api.one
	def _compute_producto(self):
		if len(self.invoice_id) > 0:
			self.producto_id = self.invoice_id.producto_id

class PanelAdmin(models.Model):
	_name = 'panel.admin'

	name = fields.Char()
	partner_activos = fields.Integer('Clientes activos', compute='_compute_clientes_activos')
	cuotas_pendientes = fields.Integer('Cuotas pendientes', compute='_compute_cuotas_pendientes')
	total_efectivo_pendiente = fields.Integer('Efectivo pendiente de cobro', compute='_compute_total_efectivo_pendiente')
	efectivo_vencido = fields.Integer('Total de efectivo vencido', compute='_compute_cuotas_vencido')	
	efectivo_moroso = fields.Integer('Total de efectivo moroso', compute='_compute_cuotas_moroso')

	@api.one
	def _compute_clientes_activos(self):
		cr = self.env.cr
		uid = self.env.uid
		partner_obj = self.pool.get('res.partner')
		partner_ids = partner_obj.search(cr, uid, [])
		partner_activos = 0
		for partner_id in partner_ids:
			cuota_obj = self.pool.get('account.move.line')
			cuota_ids = cuota_obj.search(cr, uid, [
				('partner_id', '=', partner_id),
				('amount_residual', '>', 0.0),
				('invoice_id', '!=', None),
				('reconciled', '=', False),
				])
			if len(cuota_ids) > 0:
				partner_activos += 1
		self.partner_activos = partner_activos
	
	@api.one
	def _compute_cuotas_pendientes(self):
		cr = self.env.cr
		uid = self.env.uid
		cuota_obj = self.pool.get('account.move.line')
		cuota_ids = cuota_obj.search(cr, uid, [
			('amount_residual', '>', 0.0),
			('invoice_id', '!=', None),
			('reconciled', '=', False),
			])
		self.cuotas_pendientes = len(cuota_ids)

	@api.one
	def _compute_total_efectivo_pendiente(self):
		fecha_actual = datetime.now()
		fecha_morosos = fecha_actual - timedelta(days=30)
		total_efectivo_pendiente = 0
		cr = self.env.cr
		uid = self.env.uid
		cuota_obj = self.pool.get('account.move.line')
		cuota_ids = cuota_obj.search(cr, uid, [
			('amount_residual', '>', 0.0),
			('invoice_id', '!=', None),
			('reconciled', '=', False),
			('date_maturity', '>=', fecha_morosos),
			])
		for cuota_id in cuota_ids:
			cuota_obj_id = cuota_obj.browse(cr, uid, cuota_id)
			total_efectivo_pendiente += cuota_obj_id.amount_residual
		self.total_efectivo_pendiente = total_efectivo_pendiente

	@api.one
	def _compute_cuotas_vencido(self):
		fecha_actual = datetime.now()
		efectivo_vencido = 0
		cr = self.env.cr
		uid = self.env.uid
		cuota_obj = self.pool.get('account.move.line')
		cuota_ids = cuota_obj.search(cr, uid, [
			('amount_residual', '>', 0.0),
			('invoice_id', '!=', None),
			('reconciled', '=', False),
			('date_maturity', '<=', fecha_actual),
			])
		for cuota_id in cuota_ids:
			cuota_obj_id = cuota_obj.browse(cr, uid, cuota_id)
			efectivo_vencido += cuota_obj_id.amount_residual
		self.efectivo_vencido = efectivo_vencido

	@api.one
	def _compute_cuotas_moroso(self):
		fecha_actual = datetime.now() - timedelta(days=30)
		efectivo_moroso = 0
		cr = self.env.cr
		uid = self.env.uid
		cuota_obj = self.pool.get('account.move.line')
		cuota_ids = cuota_obj.search(cr, uid, [
			('amount_residual', '>', 0.0),
			('invoice_id', '!=', None),
			('reconciled', '=', False),
			('date_maturity', '<', fecha_actual),
			])
		for cuota_id in cuota_ids:
			cuota_obj_id = cuota_obj.browse(cr, uid, cuota_id)
			efectivo_moroso += cuota_obj_id.amount_residual
		self.efectivo_moroso = efectivo_moroso

	def ver_pendientes(self, cr, uid, ids, context=None):
		fecha_actual = datetime.now()
		fecha_morosos = fecha_actual - timedelta(days=30)
		pendientes_obj = self.pool.get('account.move.line')
		pendientes_ids = pendientes_obj.search(cr, uid, [
			('amount_residual', '>', 0.0),
			('invoice_id', '!=', None),
			('reconciled', '=', False),
			('date_maturity', '>=', fecha_morosos),
			])

		model_obj = self.pool.get('ir.model.data')
		data_id = model_obj._get_id(cr, uid, 'tecs_module', 'ver_pendientes_view')
		view_id = model_obj.browse(cr, uid, data_id, context=None).res_id
		return {
			'domain': "[('id', 'in', ["+','.join(map(str, pendientes_ids))+"])]",
			'name': ('Pendientes'),
			'view_type': 'form',
			'view_mode': 'tree',
			'res_model': 'account.move.line',
			'view_id': view_id,
			'type': 'ir.actions.act_window',
		}

	def ver_vencidas(self, cr, uid, ids, context=None):
		fecha_actual = datetime.now()
		pendientes_obj = self.pool.get('account.move.line')
		pendientes_ids = pendientes_obj.search(cr, uid, [
			('amount_residual', '>', 0.0),
			('invoice_id', '!=', None),
			('reconciled', '=', False),
			('date_maturity', '<=', fecha_actual),
			])

		model_obj = self.pool.get('ir.model.data')
		data_id = model_obj._get_id(cr, uid, 'tecs_module', 'ver_pendientes_view')
		view_id = model_obj.browse(cr, uid, data_id, context=None).res_id
		return {
			'domain': "[('id', 'in', ["+','.join(map(str, pendientes_ids))+"])]",
			'name': ('Vencidas'),
			'view_type': 'form',
			'view_mode': 'tree',
			'res_model': 'account.move.line',
			'view_id': view_id,
			'type': 'ir.actions.act_window',
		}

	def ver_morosos(self, cr, uid, ids, context=None):
		fecha_actual = datetime.now()
		fecha_morosos = fecha_actual - timedelta(days=30)
		pendientes_obj = self.pool.get('account.move.line')
		pendientes_ids = pendientes_obj.search(cr, uid, [
			('amount_residual', '>', 0.0),
			('invoice_id', '!=', None),
			('reconciled', '=', False),
			('date_maturity', '<', fecha_morosos),
			])

		model_obj = self.pool.get('ir.model.data')
		data_id = model_obj._get_id(cr, uid, 'tecs_module', 'ver_pendientes_view')
		view_id = model_obj.browse(cr, uid, data_id, context=None).res_id
		context = {'state_mora': 'moroso'}
		return {
			'domain': "[('id', 'in', ["+','.join(map(str, pendientes_ids))+"])]",
			'name': ('Morosos'),
			'view_type': 'form',
			'view_mode': 'tree',
			'res_model': 'account.move.line',
			'view_id': view_id,
			'type': 'ir.actions.act_window',
		}


class ResPartner(models.Model):
	_name = 'res.partner'
	_inherit = 'res.partner'
	_order = 'score desc'

	entre_calles = fields.Char('Entre calles')
	dni_imagen = fields.Binary('DNI frontal')
	dni_imagen2 = fields.Binary('DNI posterior')
	facebook = fields.Char('Facebook')
	score = fields.Float('Score')
	state = fields.Selection([('confirm', 'Confirmado'), ('no_vender', 'No vender')], string='Estado', readonly=True, default='confirm')

	def confirm(self, cr, uid, ids, context=None):
		self.write(cr, uid, ids, {'state':'confirm'}, context=None)
		return True

	def no_vender(self, cr, uid, ids, context=None):
		self.write(cr, uid, ids, {'state':'no_vender'}, context=None)
		return True

class AccountPayment(models.Model):
	_name = 'account.payment'
	_inherit = 'account.payment'

	producto_id = fields.Char('Producto', compute="_compute_producto")

	@api.one
	def _compute_producto(self):
		self.producto_id = self.invoice_ids[0].producto_id.name

	@api.multi
	def amount_to_text(self):
		return amount_to_text_es_MX.get_amount_to_text(self, self.amount, 'centavos', 'pesos con ')
