# -*- coding: utf-8 -*-
from openerp import http

# class TecsModule(http.Controller):
#     @http.route('/tecs_module/tecs_module/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tecs_module/tecs_module/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tecs_module.listing', {
#             'root': '/tecs_module/tecs_module',
#             'objects': http.request.env['tecs_module.tecs_module'].search([]),
#         })

#     @http.route('/tecs_module/tecs_module/objects/<model("tecs_module.tecs_module"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tecs_module.object', {
#             'object': obj
#         })