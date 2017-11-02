# -*- coding: utf-8 -*-

from openerp import models, fields, api

class ExtendsInvoice(models.Model):
	_name = 'account.invoice'
	_inherit = 'account.invoice'

	periodo = fields.Selection([('semanal', 'Semanal'), ('quincenal', 'Quincenal'), ('mensual', 'Mensual')], string='Periodo', select=True, default='semanal')
	cuotas = fields.Integer('Cuotas')
	monto_cuota = fields.Float('Monto cuota')
	producto_id = fields.Many2one('product.product', 'Producto')
	descripcion = fields.Char('Descripcion')

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

	@api.one
	def delete_payment_term_line(self):
		for apt in self.payment_term_id.line_ids:
			apt.unlink()

	@api.one
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
			#self.create_payment_term_line()
		else:
			#Actualizamos el termino de pago
			print "Actualizamos payment term"
			self.payment_term_id.name = name
			self.delete_payment_term_line()
			self.create_payment_term_line()
