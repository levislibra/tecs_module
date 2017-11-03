# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import UserError
from openerp.exceptions import ValidationError

class ExtendsInvoice(models.Model):
	_name = 'account.invoice'
	_inherit = 'account.invoice'

	periodo = fields.Selection([('semanal', 'Semanal'), ('quincenal', 'Quincenal'), ('mensual', 'Mensual')], string='Periodo', select=True, default='semanal')
	cuotas = fields.Integer('Cuotas')
	monto_cuota = fields.Float('Monto cuota')
	producto_id = fields.Many2one('product.product', 'Producto')
	descripcion = fields.Char('Descripcion')
	#payment_term_id = fields.Many2one('account.payment.term', 'Plazo de pago', compute='computar_plazo')

	invoice_line_id = fields.Many2one('account.invoice.line', 'Linea de factura')

	@api.one
	def actualizar(self):
		print self.producto_id
		if len(self.producto_id) > 0:
			print "producto != False"
			if self.descripcion and len(self.descripcion) > 0:
				descripcion = self.descripcion
			else:
				descripcion = self.producto_id.name

			print len(self.invoice_line_id)
			if len(self.invoice_line_id) == 0:
				print "creando el AIL"
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
				print "Actualizando el AIL"
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
			print self.dias_periodo() * i
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
		print "computar plazo"
		print self.payment_term_id
		print self.periodo
		name = str(self.cuotas) + " cuotas " + str(self.periodo)
		if len(self.payment_term_id) == 0:
			#Creamos el termino de pago
			print "Creamos el term payment"
			company_id = self.env['res.users'].browse(self.env.uid).company_id.id
			pti = self.env['account.payment.term'].create({
					'name': name,
					'company_id': company_id,
					'active': True,
				})
			self.payment_term_id = pti.id
			print self.payment_term_id
			self.delete_payment_term_line()
			self.create_payment_term_line()
		else:
			#Actualizamos el termino de pago
			print "Actualizamos payment term"
			self.payment_term_id.name = name
			self.delete_payment_term_line()
			self.create_payment_term_line()

	@api.onchange('periodo', 'cuotas', 'monto_cuota', 'producto_id', 'descripcion')
	def onchange_values(self):
		self.actualizar()

	@api.one
	@api.constrains('state')
	def _check_values(self):
		if self.state == 'open':
			if self.cuotas != len(self.payment_term_id.line_ids):
				raise UserError("Debe Computar plazo, ya que la cantidad de cuotas no coinciden.")
			if self.monto_cuota != self.payment_term_id.line_ids[0].value_amount:
				raise UserError("Debe Computar plazo, ya que el monto de cuota no coincide.")
			if len(self.payment_term_id.line_ids) <= 1:
				raise UserError("La cantidad de cuotas debe ser mayor a una.")
			if self.dias_periodo() != self.payment_term_id.line_ids[1].days:
				raise UserError("Debe Computar plazo, ya que el periodo de las cuotas no coinciden.")


class AccountPayment(models.Model):
    # This OpenERP object inherits from cheques.de.terceros
    # to add a new float field
    _inherit = 'account.payment'
    _name = 'account.payment'
    
    apunte_contable_id = fields.Many2one('account.move.line', 'Cuota', domain="[('partner_id', '=', partner_id), ('account_id', '=', property_account_receivable_id), ('reconciled', '=', False), ('debit', '>', 0)]")
    property_account_receivable_id = fields.Many2one('account.account', 'Cuenta', compute='_compute_account_receivable')

    @api.one
    @api.onchange('partner_id')
    def _compute_account_receivable(self):
    	print self.partner_id
    	if len(self.partner_id) > 0:
    		self.property_account_receivable_id = self.partner_id.property_account_receivable_id.id

    @api.onchange('apunte_contable_id')
    def compute_amount(self):
    	self.amount = self.apunte_contable_id.debit

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'
	_name = 'account.move.line'

	_order = 'date_maturity desc'
	_rec_name = 'display_name'
	display_name = fields.Char('Name', compute='_compute_name')


	@api.one
	def _compute_name(self):
		self.display_name = str(self.date_maturity) + ' ' + str(self.debit)