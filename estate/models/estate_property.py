"""
This module defines the estate property model.
"""

from odoo import models, fields, api, exceptions
from odoo.tools import float_compare, float_is_zero
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta

class EstateProperty(models.Model):
    """
    This class represents an estate property.
    """
    _name = "estate.property"
    _description = "Real Estate Property"
    _order = "id desc"  # Ajout de l'ordre par défaut
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Champs de base
    name = fields.Char(required=True, tracking=True)
    description = fields.Html()
    date_availability = fields.Date(
        string="Available From",
        default=lambda self: fields.Date.today() + relativedelta(months=3),
        tracking=True
    )
    
    # Prix et surface
    expected_price = fields.Float(required=True, tracking=True)
    selling_price = fields.Float(readonly=True, copy=False, tracking=True)
    best_price = fields.Float(compute="_compute_best_price", store=True)
    
    # Caractéristiques
    bedrooms = fields.Integer(default=2)
    living_area = fields.Float(string="Living Area (m²)")
    facades = fields.Integer()
    garage = fields.Boolean()
    garden = fields.Boolean()
    garden_area = fields.Float(string="Garden Area (m²)")
    garden_orientation = fields.Selection([
        ('north', 'North'),
        ('south', 'South'),
        ('east', 'East'),
        ('west', 'West')
    ])
    total_area = fields.Float(
        compute='_compute_total_area',
        string='Total Area (m²)',
        store=True
    )
    
    # Relations
    property_type_id = fields.Many2one(
        'estate.property.type',
        string='Property Type',
        required=True,
        tracking=True
    )
    tag_ids = fields.Many2many('estate.property.tag', string="Tags")
    offer_ids = fields.One2many('estate.property.offer', 'property_id', string="Offers")
    buyer_id = fields.Many2one('res.partner', string='Buyer', copy=False, tracking=True)
    user_id = fields.Many2one(
        'res.users',
        string='Salesperson',
        default=lambda self: self.env.user,
        tracking=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )
    
    # Gestion
    active = fields.Boolean(default=True)
    state = fields.Selection([
        ('new', 'New'),
        ('offer_received', 'Offer Received'),
        ('offer_accepted', 'Offer Accepted'),
        ('sold', 'Sold'),
        ('cancelled', 'Cancelled')
    ], required=True, default='new', tracking=True, copy=False)

    reference = fields.Char(
        'Reference',
        required=True,
        copy=False,
        readonly=True,
        default='New'
    )

    _sql_constraints = [
        ('check_expected_price', 'CHECK(expected_price > 0)',
         'Expected price must be strictly positive'),
        ('check_selling_price', 'CHECK(selling_price >= 0)',
         'Selling price must be positive'),
    ]

    @api.depends('living_area', 'garden_area')
    def _compute_total_area(self):
        for record in self:
            record.total_area = record.living_area + record.garden_area

    @api.depends('offer_ids.price')
    def _compute_best_price(self):
        for prop in self:
            prop.best_price = max(prop.offer_ids.mapped('price') or [0.0])

    @api.onchange('garden')
    def _onchange_garden(self):
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = 'north'
        else:
            self.garden_area = 0
            self.garden_orientation = False

    @api.constrains('expected_price', 'selling_price')
    def _check_price_difference(self):
        for record in self:
            if not float_is_zero(record.selling_price, precision_digits=2):
                if float_compare(record.selling_price, record.expected_price * 0.9, precision_digits=2) < 0:
                    raise ValidationError(
                        "The selling price cannot be lower than 90% of the expected price."
                    )

    def action_sold(self):
        for prop in self:
            if prop.state == 'cancelled':
                raise UserError("Cancelled properties cannot be sold.")
            if not prop.offer_ids.filtered(lambda o: o.status == 'accepted'):
                raise UserError("Cannot sell a property without an accepted offer.")
            prop.state = 'sold'
            # Créer une activité pour le service financier
            self.env['mail.activity'].create({
                'activity_type_id': self.env.ref('estate.mail_activity_property_sold').id,
                'note': f'Property {prop.name} has been sold. Please create invoice.',
                'user_id': self.env.user.id,
                'res_id': prop.id,
                'res_model_id': self.env['ir.model']._get(self._name).id,
            })
        return True

    def action_cancel(self):
        for prop in self:
            if prop.state == 'sold':
                raise UserError("Sold properties cannot be cancelled.")
            prop.state = 'cancelled'
            # Annuler toutes les offres en cours
            prop.offer_ids.filtered(lambda o: o.status not in ['accepted', 'refused']).write({
                'status': 'refused'
            })
        return True

    def unlink(self):
        if not self.env.user.has_group('estate.estate_group_manager'):
            raise UserError("Only managers can delete properties.")
        if any(prop.state not in ['new', 'cancelled'] for prop in self):
            raise UserError("Only new and cancelled properties can be deleted.")
        return super().unlink()

    @api.model
    def _valid_field_parameter(self, field, name):
        return name == 'tracking' or super()._valid_field_parameter(field, name)

    def open_offers(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Property Offers',
            'res_model': 'estate.property.offer',
            'view_mode': 'tree,form',
            'domain': [('property_id', '=', self.id)],
            'context': {'default_property_id': self.id},
        }

    def action_view_offers(self):
        return self.open_offers()

    @api.model
    def create(self, vals):
        if vals.get('reference', 'New') == 'New':
            vals['reference'] = self.env['ir.sequence'].next_by_code('estate.property') or 'New'
        return super().create(vals)

# Ensure the file ends with a newline 