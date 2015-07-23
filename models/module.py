# -*- coding: utf-8 -*-

import logging
from openerp.osv import osv, fields

_logger = logging.getLogger(__name__)

class module(osv.osv):
    _inherit = "ir.module.module"

    def _get_model_info(self, cr, uid, model_id, context=None):
        model_obj = self.pool.get('ir.model')
        model = model_obj.browse(cr, uid, model_id, context=context)
        return '<td>%s</td><td>%s</td>' % (model.name, model.model)

    def _get_field_info(self, cr, uid, field_id, context=None):
        def get_field_prefix(field):
            return [field.field_description, field.name, field.model_id.name, field.model_id.model]

        def get_field_postfix(field):
            retval = ['', '']
            if field.required:
                retval[0] = 'x'
            if field.readonly:
                retval[1] = 'x'
            return retval

        def get_field_specific_info(field):
            retval = getattr(field, 'relation') if field.ttype in ['many2many', 'many2one', 'one2many'] else ''
            return retval

        field_obj = self.pool.get('ir.model.fields')
        field = field_obj.browse(cr, uid, field_id, context=context)

        return '<td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>' % (
            get_field_prefix(field)[0],
            get_field_prefix(field)[1],
            get_field_prefix(field)[2],
            get_field_prefix(field)[3],
            field.ttype,
            get_field_specific_info(field),
            get_field_postfix(field)[0],
            get_field_postfix(field)[0],
            )

    def _get_data_info(self, cr, uid, res, context=None):
        model_obj = self.pool.get('ir.model')
        model_id = model_obj.search(cr, uid, [('model', '=', res.model)])
        model = model_obj.browse(cr, uid, model_id, context=context)[0]
        return '<td>%s.%s</td><td>%s</td><td>%s</td><td>%i</td>' % (res.module, res.name, model.name, model.model, res.id)

    def _get_model_data(self, cr, uid, ids, field_name=None, arg=None, context=None):
        # early opt-out if nothing to do
        assert field_name is None or set(['models_by_module', 'fields_by_module', 'data_by_module']) & set(field_name)
        res = {}
        model_data_obj = self.pool.get('ir.model.data')

        ignored_models = [
            'ir.ui.view',
            'ir.ui.menu',
            'ir.actions.report.xml',
            'ir.module.module',
            'ir.module.category']
        model_data_search = [('model', 'not in',  ignored_models)]

        for module_rec in self.browse(cr, uid, ids, context=context):
            # Only fetch for modules in some sort of installed state
            if module_rec.state not in ('installed', 'to upgrade', 'to remove'):
                continue

            res[module_rec.id] = {
                'models_by_module': [],
                'fields_by_module': [],
                'data_by_module': []
            }

            model_data_ids = model_data_obj.search(cr, uid, [('module', '=', module_rec.name)] + model_data_search, context=context)
            model_data = model_data_obj.browse(cr, uid, model_data_ids, context=context)

            # For each one of the models, get the names of these ids.
            # We use try except, because views or menus may not exist.
            try:
                for rec in model_data:
                    if rec.model == 'ir.model':
                        res[module_rec.id]['models_by_module'].append(self._get_model_info(cr, uid, rec.res_id, context=context))
                    elif rec.model == 'ir.model.fields':
                        res[module_rec.id]['fields_by_module'].append(self._get_field_info(cr, uid, rec.res_id, context=context))
                    else:
                        res[module_rec.id]['data_by_module'].append(self._get_data_info(cr, uid, rec, context=context))
            except KeyError, e:
                _logger.warning('Data not found for items of %s', module_rec.name)
            except AttributeError, e:
                _logger.warning('Data not found for items of %s %s', module_rec.name, str(e))
            except Exception, e:
                _logger.warning('Unknown error while fetching data of %s', module_rec.name, exc_info=True)

        for key in res.iterkeys():
            res[key]['models_by_module'] = '<table width="100%"><tr>' \
                + '<th colspan="2" style="text-align: center;">Models</th></tr><tr>' \
                + '<th>Name</th><th>Technical Name</th></tr><tr>' \
                + '</tr><tr>'.join(sorted(res[key]['models_by_module'])) \
                + '</tr></table>'
            res[key]['fields_by_module'] = '<table width="100%"><tr>' \
                + '<th colspan="8" style="text-align: center;">Fields</th></tr><tr>' \
                + '<th>Name</th><th>Technical Name</th>' \
                + '<th>Model</th><th>ModelTechnical Name</th>' \
                + '<th>Type</th><th>Object Relation</th>' \
                + '<th>Required</th><th>Readonly</th></tr><tr>' \
                + '</tr><tr>'.join(sorted(res[key]['fields_by_module'])) \
                + '</tr></table>'
            res[key]['data_by_module'] = '<table width="100%"><tr>' \
                + '<th colspan="4" style="text-align: center;">Data Records</th></tr><tr>' \
                + '<th>XML ID</th><th>Model</th><th>Model Technical Name</th><th>ID</th></tr><tr>' \
                + '</tr><tr>'.join(sorted(res[key]['data_by_module'])) \
                + '</tr></table>'
        return res

    _columns = {
        'models_by_module': fields.function(_get_model_data, string='Models', type='html', multi="metadata"),
        'fields_by_module': fields.function(_get_model_data, string='Fields', type='html', multi="metadata"),
        'data_by_module': fields.function(_get_model_data, string='Data', type='html', multi="metadata"),
    }
