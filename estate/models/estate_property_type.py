from odoo import models, fields, api

class EstatePropertyType(models.Model):
    _name = "estate.property.type"
    _description = "Property Type"
    _order = "sequence, name"

    name = fields.Char(required=True)
    sequence = fields.Integer('Sequence', default=10)
    property_ids = fields.One2many('estate.property', 'property_type_id', string='Properties')
    offer_ids = fields.One2many(
        'estate.property.offer',
        'property_type_id',
        string='Offers'
    )
    property_count = fields.Integer(
        compute='_compute_property_count',
        string='Property Count'
    )
    offer_count = fields.Integer(
        compute='_compute_offer_count',
        string='Offer Count'
    )

    _sql_constraints = [
        ('unique_name', 'UNIQUE(name)',
         'Property type name must be unique.')
    ]

    @api.depends('property_ids')
    def _compute_property_count(self):
        for record in self:
            record.property_count = len(record.property_ids)

    @api.depends('offer_ids')
    def _compute_offer_count(self):
        for record in self:
            record.offer_count = len(record.offer_ids)

    def action_view_properties(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Properties',
            'res_model': 'estate.property',
            'view_mode': 'kanban,tree,form',
            'domain': [('property_type_id', '=', self.id)],
            'context': {'default_property_type_id': self.id},
        }

    def action_view_offers(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Offers',
            'res_model': 'estate.property.offer',
            'view_mode': 'tree,form',
            'domain': [('property_type_id', '=', self.id)],
            'context': {'default_property_type_id': self.id},
        }

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.name} ({len(record.property_ids)} properties)"
            result.append((record.id, name))
        return result 