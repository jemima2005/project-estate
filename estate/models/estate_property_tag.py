# estate_property_tag.py
"""
This module defines property tags for categorization.
"""

from odoo import models, fields


class EstatePropertyTag(models.Model):
    """
    Represents tags that can be applied to properties.
    Provides functionality for property categorization and filtering.
    """
    _name = "estate.property.tag"
    _description = "Property Tag"
    _order = "name"

    name = fields.Char(required=True)
    color = fields.Integer(string="Color Index")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('unique_tag_name', 'UNIQUE(name)',
         'Tag name must be unique!')
    ]

    def name_get(self):
        """Override name_get to customize display name format."""
        return [(tag.id, tag.name.upper()) for tag in self]
