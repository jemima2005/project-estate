from datetime import timedelta
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Property Offer"
    _order = "price desc"
    _rec_name = "price"

    price = fields.Float('Price', required=True)
    status = fields.Selection(
        selection=[
            ('accepted', 'Accepted'),
            ('refused', 'Refused')
        ],
        copy=False,
        tracking=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string="Partner",
        required=True,
        tracking=True
    )
    property_id = fields.Many2one(
        'estate.property',
        required=True,
        ondelete='cascade'
    )
    create_date = fields.Datetime('Creation Date', readonly=True)
    validity = fields.Integer(
        string='Validity (days)',
        default=7,
        tracking=True
    )
    date_deadline = fields.Date(
        compute='_compute_date_deadline',
        inverse='_inverse_date_deadline',
        store=True,
        tracking=True
    )
    property_type_id = fields.Many2one(
        'estate.property.type',
        related='property_id.property_type_id',
        store=True,
        string="Property Type"
    )
    salesperson_id = fields.Many2one(
        "res.users", 
        string="Salesperson",
        related="property_id.user_id", 
        store=True
    )

    _sql_constraints = [
        ('check_price_positive', 'CHECK(price > 0)',
         'Offer price must be strictly positive'),
    ]

    @api.depends('create_date', 'validity')
    def _compute_date_deadline(self):
        for offer in self:
            if offer.create_date:
                offer.date_deadline = fields.Date.to_date(offer.create_date) + timedelta(days=offer.validity)
            else:
                offer.date_deadline = fields.Date.today() + timedelta(days=offer.validity)

    def _inverse_date_deadline(self):
        for offer in self:
            if offer.create_date and offer.date_deadline:
                offer.validity = (offer.date_deadline - fields.Date.to_date(offer.create_date)).days
            else:
                offer.validity = (offer.date_deadline - fields.Date.today()).days

    def action_accept(self):
        if self.filtered(lambda o: o.property_id.state not in ['new', 'offer_received']):
            raise UserError("Cannot accept offer if property is not in 'New' or 'Offer Received' state.")
            
        for offer in self:
            # Refuse other offers
            offer.property_id.offer_ids.filtered(lambda o: o != offer).write({
                'status': 'refused'
            })
            
            # Accept current offer
            offer.write({
                'status': 'accepted'
            })
            
            # Update property
            offer.property_id.write({
                'state': 'offer_accepted',
                'selling_price': offer.price,
                'buyer_id': offer.partner_id.id
            })
        return True

    def action_refuse(self):
        for offer in self:
            if offer.status == 'accepted':
                offer.property_id.write({
                    'state': 'offer_received',
                    'selling_price': 0,
                    'buyer_id': False
                })
            offer.status = 'refused'
        return True

    @api.model
    def create(self, vals):
        property_id = self.env['estate.property'].browse(vals.get('property_id'))
        
        # Vérifications
        if property_id.state in ['offer_accepted', 'sold', 'cancelled']:
            raise UserError(f"Cannot create offer for property in {property_id.state} state")
            
        # Créer l'offre
        offer = super().create(vals)
        
        # Mettre à jour l'état de la propriété
        if property_id.state == 'new':
            property_id.state = 'offer_received'
            
        # Vérifier si c'est la meilleure offre
        if offer.price < property_id.best_price:
            raise UserError(f"Cannot create offer: there is already a better offer (${property_id.best_price:,.2f})")
            
        return offer