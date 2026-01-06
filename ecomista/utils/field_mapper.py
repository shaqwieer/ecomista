# Copyright (c) 2026, Shaqwieer and contributors
# For license information, please see license.txt

"""
Field Mapper Utility - Generic Mapping Layer for Ecomista

This module provides a generic data mapping utility that transforms data
from source format to target format based on Field Mapping configurations.

Usage:
    from ecomista.utils import FieldMapper, map_data
    
    # Quick mapping using connection entity
    result = map_data(source_data, "Integration Connection Entity Name")
    
    # Or use the class directly for more control
    mapper = FieldMapper(entity_name="Order-Invoice Entity")
    result = mapper.transform(source_data)
"""

import json
from typing import Any

import frappe
from frappe import _

from ecomista.utils.transformers import get_transformer


class FieldMapper:
    """
    Generic Field Mapper that transforms source data to target format
    based on Field Mapping configurations from Integration Connection Entity.
    
    Attributes:
        entity_name: Name of the Integration Connection Entity
        mappings: List of field mapping configurations
        connection: Integration Connection document
    """
    
    def __init__(
        self,
        entity_name: str | None = None,
        mappings: list[dict] | None = None,
        connection_name: str | None = None,
    ):
        """
        Initialize the FieldMapper.
        
        Args:
            entity_name: Name of Integration Connection Entity to load mappings from
            mappings: Direct list of mapping dictionaries (alternative to entity_name)
            connection_name: Name of Integration Connection (used with entity_type)
        """
        self.entity_name = entity_name
        self.connection_name = connection_name
        self.mappings: list[dict] = []
        self.entity_doc = None
        self.connection_doc = None
        
        if entity_name:
            self._load_from_entity(entity_name)
        elif mappings:
            self.mappings = mappings
    
    def _load_from_entity(self, entity_name: str) -> None:
        """Load field mappings from Integration Connection Entity."""
        try:
            self.entity_doc = frappe.get_doc("Integration Connection Entity", entity_name)
            self.connection_name = self.entity_doc.integration_connection
            
            if self.connection_name:
                self.connection_doc = frappe.get_doc(
                    "Integration Connection", self.connection_name
                )
            
            # Load mappings from child table
            self.mappings = []
            for mapping in self.entity_doc.mapping_fields or []:
                self.mappings.append({
                    "source_field": mapping.source_field,
                    "target_field": mapping.target_field,
                    "transformation": mapping.transformation,
                    "transform_config": mapping.transform_config,
                    "default_value": mapping.default_value,
                    "is_child_mapping": mapping.is_child_mapping,
                    "child_source_path": mapping.child_source_path,
                    "child_target_path": mapping.child_target_path,
                })
        except frappe.DoesNotExistError:
            frappe.throw(_("Integration Connection Entity '{0}' not found").format(entity_name))
    
    def transform(self, source_data: dict) -> dict:
        """
        Transform source data to target format using configured mappings.
        
        Args:
            source_data: Source data dictionary to transform
            
        Returns:
            Transformed data dictionary in target format
        """
        if not self.mappings:
            frappe.throw(_("No field mappings configured"))
        
        result = {}
        child_mappings = []
        
        # Separate regular and child mappings
        for mapping in self.mappings:
            if mapping.get("is_child_mapping"):
                child_mappings.append(mapping)
            else:
                self._apply_mapping(source_data, result, mapping)
        
        # Process child mappings (nested arrays like line_items)
        for mapping in child_mappings:
            self._apply_child_mapping(source_data, result, mapping)
        
        return result
    
    def _apply_mapping(
        self, source_data: dict, result: dict, mapping: dict
    ) -> None:
        """
        Apply a single field mapping transformation.
        
        Args:
            source_data: Source data dictionary
            result: Result dictionary to populate
            mapping: Mapping configuration
        """
        source_field = mapping.get("source_field", "")
        target_field = mapping.get("target_field", "")
        transformation = mapping.get("transformation", "Direct")
        transform_config = mapping.get("transform_config")
        default_value = mapping.get("default_value")
        
        # Get source value using dot notation path
        source_value = self._get_nested_value(source_data, source_field)
        
        # Apply transformation
        transformer = get_transformer(transformation)
        transformed_value = transformer(
            value=source_value,
            config=self._parse_config(transform_config),
            default=default_value,
            source_data=source_data,
            mapping=mapping,
        )
        
        # Set target value using dot notation path
        self._set_nested_value(result, target_field, transformed_value)
    
    def _apply_child_mapping(
        self, source_data: dict, result: dict, mapping: dict
    ) -> None:
        """
        Apply child/nested mapping for arrays like line_items.
        
        Args:
            source_data: Source data dictionary
            result: Result dictionary to populate
            mapping: Child mapping configuration
        """
        child_source_path = mapping.get("child_source_path", "")
        child_target_path = mapping.get("child_target_path", "")
        source_field = mapping.get("source_field", "")
        target_field = mapping.get("target_field", "")
        transformation = mapping.get("transformation", "Direct")
        transform_config = mapping.get("transform_config")
        default_value = mapping.get("default_value")
        
        # Get source array
        source_array = self._get_nested_value(source_data, child_source_path)
        
        if not isinstance(source_array, list):
            return
        
        # Get or create target array
        target_array = self._get_nested_value(result, child_target_path)
        if target_array is None:
            target_array = [{} for _ in source_array]
            self._set_nested_value(result, child_target_path, target_array)
        
        # Ensure target array has enough items
        while len(target_array) < len(source_array):
            target_array.append({})
        
        # Apply mapping to each item
        transformer = get_transformer(transformation)
        for idx, source_item in enumerate(source_array):
            source_value = self._get_nested_value(source_item, source_field)
            
            transformed_value = transformer(
                value=source_value,
                config=self._parse_config(transform_config),
                default=default_value,
                source_data=source_item,
                mapping=mapping,
            )
            
            self._set_nested_value(target_array[idx], target_field, transformed_value)
    
    def _get_nested_value(self, data: dict, path: str) -> Any:
        """
        Get value from nested dictionary using dot notation.
        
        Args:
            data: Source dictionary
            path: Dot-separated path (e.g., "customer.email")
            
        Returns:
            Value at the path or None if not found
        """
        if not path or not data:
            return None
        
        keys = path.split(".")
        current = data
        
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            elif isinstance(current, list) and key.isdigit():
                idx = int(key)
                current = current[idx] if idx < len(current) else None
            else:
                return None
            
            if current is None:
                return None
        
        return current
    
    def _set_nested_value(self, data: dict, path: str, value: Any) -> None:
        """
        Set value in nested dictionary using dot notation.
        
        Args:
            data: Target dictionary
            path: Dot-separated path (e.g., "customer.email")
            value: Value to set
        """
        if not path:
            return
        
        keys = path.split(".")
        current = data
        
        for i, key in enumerate(keys[:-1]):
            if key not in current:
                # Check if next key is a digit (array index)
                next_key = keys[i + 1]
                if next_key.isdigit():
                    current[key] = []
                else:
                    current[key] = {}
            current = current[key]
        
        final_key = keys[-1]
        if isinstance(current, list) and final_key.isdigit():
            idx = int(final_key)
            while len(current) <= idx:
                current.append({})
            current[idx] = value
        else:
            current[final_key] = value
    
    def _parse_config(self, config: str | None) -> dict:
        """Parse transform_config JSON string to dictionary."""
        if not config:
            return {}
        
        try:
            return json.loads(config)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def get_entity_info(self) -> dict:
        """Get information about the loaded entity."""
        return {
            "entity_name": self.entity_name,
            "connection_name": self.connection_name,
            "entity_type": self.entity_doc.entity_type if self.entity_doc else None,
            "target_endpoint": self.entity_doc.target_endpoint if self.entity_doc else None,
            "mapping_count": len(self.mappings),
        }


def map_data(
    source_data: dict,
    entity_name: str | None = None,
    mappings: list[dict] | None = None,
) -> dict:
    """
    Quick function to map source data to target format.
    
    Args:
        source_data: Source data dictionary to transform
        entity_name: Name of Integration Connection Entity
        mappings: Direct list of mapping dictionaries
        
    Returns:
        Transformed data dictionary
        
    Example:
        >>> source = {"order_number": "1001", "total_price": "99.99"}
        >>> result = map_data(source, entity_name="Shopify Order Entity")
    """
    mapper = FieldMapper(entity_name=entity_name, mappings=mappings)
    return mapper.transform(source_data)


def get_mapper_for_entity(entity_name: str) -> FieldMapper:
    """
    Get a FieldMapper instance for a specific entity.
    
    Args:
        entity_name: Name of Integration Connection Entity
        
    Returns:
        Configured FieldMapper instance
    """
    return FieldMapper(entity_name=entity_name)


def get_mapper_for_connection(
    connection_name: str, entity_type: str
) -> FieldMapper:
    """
    Get a FieldMapper for a connection and entity type.
    
    Args:
        connection_name: Name of Integration Connection
        entity_type: Entity type (Order-Invoice, Customer, Product)
        
    Returns:
        Configured FieldMapper instance
    """
    entity = frappe.get_value(
        "Integration Connection Entity",
        {
            "integration_connection": connection_name,
            "entity_type": entity_type,
        },
        "name",
    )
    
    if not entity:
        frappe.throw(
            _("No entity mapping found for connection '{0}' and type '{1}'").format(
                connection_name, entity_type
            )
        )
    
    return FieldMapper(entity_name=entity)
