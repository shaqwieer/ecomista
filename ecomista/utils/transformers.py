# Copyright (c) 2026, Shaqwieer and contributors
# For license information, please see license.txt

"""
Transformers Module - Data Transformation Handlers for Field Mapping

This module provides transformation functions that convert source values
to target values based on transformation type configuration.

Supported Transformations:
    - Direct: Copy value as-is
    - Lookup: Query DocType for value
    - Formula: Evaluate Python expression
    - Cast: Type conversion (int, float, string, date, etc.)
    - Default: Use default value if source is empty

Custom transformers can be registered using:
    from ecomista.utils import register_transformer
    
    @register_transformer("MyTransform")
    def my_transform(value, config, default, source_data, mapping):
        return transformed_value
"""

import re
from datetime import datetime
from typing import Any, Callable

import frappe
from frappe import _
from frappe.utils import (
    cint,
    cstr,
    flt,
    getdate,
    get_datetime,
    nowdate,
    now_datetime,
)


# Type alias for transformer function signature
TransformerFunc = Callable[[Any, dict, Any, dict, dict], Any]


class TransformerRegistry:
    """
    Registry for transformation functions.
    
    Allows registering custom transformers that can be referenced
    by name in Field Mapping configurations.
    """
    
    _transformers: dict[str, TransformerFunc] = {}
    
    @classmethod
    def register(cls, name: str, func: TransformerFunc) -> None:
        """Register a transformer function."""
        cls._transformers[name] = func
    
    @classmethod
    def get(cls, name: str) -> TransformerFunc | None:
        """Get a transformer function by name."""
        return cls._transformers.get(name)
    
    @classmethod
    def list_transformers(cls) -> list[str]:
        """List all registered transformer names."""
        return list(cls._transformers.keys())


def register_transformer(name: str) -> Callable[[TransformerFunc], TransformerFunc]:
    """
    Decorator to register a transformer function.
    
    Example:
        @register_transformer("Uppercase")
        def uppercase_transform(value, config, default, source_data, mapping):
            return str(value).upper() if value else default
    """
    def decorator(func: TransformerFunc) -> TransformerFunc:
        TransformerRegistry.register(name, func)
        return func
    return decorator


def get_transformer(name: str) -> TransformerFunc:
    """
    Get transformer function by name.
    
    Args:
        name: Transformer name (Direct, Lookup, Formula, Cast, Default)
        
    Returns:
        Transformer function
        
    Raises:
        ValueError: If transformer not found
    """
    transformer = TransformerRegistry.get(name)
    if transformer is None:
        frappe.throw(_("Unknown transformation type: {0}").format(name))
    return transformer


# ============================================================================
# Built-in Transformers
# ============================================================================


@register_transformer("Direct")
def transform_direct(
    value: Any,
    config: dict,
    default: Any,
    source_data: dict,
    mapping: dict,
) -> Any:
    """
    Direct transformation - returns value as-is or default if empty.
    
    Config options:
        - strip: bool - Strip whitespace from strings
        - lower: bool - Convert to lowercase
        - upper: bool - Convert to uppercase
    """
    if value is None or value == "":
        return default
    
    result = value
    
    if isinstance(result, str):
        if config.get("strip", False):
            result = result.strip()
        if config.get("lower", False):
            result = result.lower()
        if config.get("upper", False):
            result = result.upper()
    
    return result


@register_transformer("Lookup")
def transform_lookup(
    value: Any,
    config: dict,
    default: Any,
    source_data: dict,
    mapping: dict,
) -> Any:
    """
    Lookup transformation - queries a DocType to find a related value.
    
    Config options:
        - doctype: str - DocType to query (required)
        - match_field: str - Field to match against source value
        - return_field: str - Field to return (default: "name")
        - filters: dict - Additional filters
        - create_if_missing: bool - Create document if not found
        - create_values: dict - Values for new document
    
    Example config:
        {
            "doctype": "Customer",
            "match_field": "email",
            "return_field": "name"
        }
    """
    if value is None or value == "":
        return default
    
    doctype = config.get("doctype")
    if not doctype:
        frappe.log_error("Lookup transformer: missing doctype in config")
        return default
    
    match_field = config.get("match_field", "name")
    return_field = config.get("return_field", "name")
    additional_filters = config.get("filters", {})
    
    # Build filters
    filters = {match_field: value}
    filters.update(additional_filters)
    
    # Query the doctype
    result = frappe.get_value(doctype, filters, return_field)
    
    if result:
        return result
    
    # Handle create_if_missing
    if config.get("create_if_missing"):
        create_values = config.get("create_values", {})
        create_values[match_field] = value
        
        try:
            doc = frappe.get_doc({
                "doctype": doctype,
                **create_values
            })
            doc.insert(ignore_permissions=True)
            return doc.get(return_field)
        except Exception as e:
            frappe.log_error(f"Lookup transformer: failed to create {doctype}: {e}")
            return default
    
    return default


@register_transformer("Formula")
def transform_formula(
    value: Any,
    config: dict,
    default: Any,
    source_data: dict,
    mapping: dict,
) -> Any:
    """
    Formula transformation - evaluates a Python expression.
    
    Available variables in formula:
        - value: The source field value
        - source: The full source data dictionary
        - frappe: Frappe module
        - flt, cint, cstr: Type conversion utilities
        - getdate, get_datetime: Date utilities
        - nowdate, now_datetime: Current date/time
    
    Config options:
        - expression: str - Python expression to evaluate (required)
    
    Example config:
        {"expression": "flt(value) * 1.1"}  # Add 10%
        {"expression": "source.get('first_name', '') + ' ' + source.get('last_name', '')"}
    """
    expression = config.get("expression")
    if not expression:
        return value if value is not None else default
    
    # Safe evaluation context
    eval_context = {
        "value": value,
        "source": source_data,
        "frappe": frappe,
        "flt": flt,
        "cint": cint,
        "cstr": cstr,
        "getdate": getdate,
        "get_datetime": get_datetime,
        "nowdate": nowdate,
        "now_datetime": now_datetime,
        "len": len,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "list": list,
        "dict": dict,
        "round": round,
        "abs": abs,
        "min": min,
        "max": max,
        "sum": sum,
    }
    
    try:
        result = eval(expression, {"__builtins__": {}}, eval_context)
        return result if result is not None else default
    except Exception as e:
        frappe.log_error(f"Formula transformer error: {e}\nExpression: {expression}")
        return default


@register_transformer("Cast")
def transform_cast(
    value: Any,
    config: dict,
    default: Any,
    source_data: dict,
    mapping: dict,
) -> Any:
    """
    Cast transformation - converts value to specified type.
    
    Config options:
        - type: str - Target type (required)
            Supported: int, float, string, bool, date, datetime, json, list
        - format: str - Format string for date/datetime parsing
        - separator: str - Separator for list conversion (default: ",")
    
    Example config:
        {"type": "int"}
        {"type": "float"}
        {"type": "date", "format": "%Y-%m-%d"}
        {"type": "list", "separator": ","}
    """
    if value is None or value == "":
        return default
    
    cast_type = config.get("type", "string")
    
    try:
        if cast_type == "int":
            return cint(value)
        
        elif cast_type == "float":
            return flt(value)
        
        elif cast_type == "string":
            return cstr(value)
        
        elif cast_type == "bool":
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes", "on")
            return bool(value)
        
        elif cast_type == "date":
            date_format = config.get("format")
            if date_format and isinstance(value, str):
                return datetime.strptime(value, date_format).date()
            return getdate(value)
        
        elif cast_type == "datetime":
            date_format = config.get("format")
            if date_format and isinstance(value, str):
                return datetime.strptime(value, date_format)
            return get_datetime(value)
        
        elif cast_type == "json":
            import json
            if isinstance(value, str):
                return json.loads(value)
            return value
        
        elif cast_type == "list":
            if isinstance(value, list):
                return value
            if isinstance(value, str):
                separator = config.get("separator", ",")
                return [item.strip() for item in value.split(separator)]
            return [value]
        
        else:
            frappe.log_error(f"Cast transformer: unknown type '{cast_type}'")
            return value
            
    except Exception as e:
        frappe.log_error(f"Cast transformer error: {e}\nValue: {value}, Type: {cast_type}")
        return default


@register_transformer("Default")
def transform_default(
    value: Any,
    config: dict,
    default: Any,
    source_data: dict,
    mapping: dict,
) -> Any:
    """
    Default transformation - returns default value, optionally based on conditions.
    
    Config options:
        - value: Any - Static default value
        - field: str - Get value from another source field
        - expression: str - Evaluate expression for default
        - condition: str - Only use default if condition is true
    
    Example config:
        {"value": "Unknown"}
        {"field": "billing_address.country"}
        {"expression": "nowdate()"}
    """
    # If source value exists and is not empty, return it
    if value is not None and value != "":
        # Check condition
        condition = config.get("condition")
        if condition:
            eval_context = {
                "value": value,
                "source": source_data,
                "__builtins__": {},
            }
            try:
                if eval(condition, {"__builtins__": {}}, eval_context):
                    pass  # Continue to apply default
                else:
                    return value
            except Exception:
                return value
        else:
            return value
    
    # Apply default
    if "value" in config:
        return config["value"]
    
    if "field" in config:
        from ecomista.utils.field_mapper import FieldMapper
        mapper = FieldMapper()
        return mapper._get_nested_value(source_data, config["field"])
    
    if "expression" in config:
        eval_context = {
            "source": source_data,
            "frappe": frappe,
            "nowdate": nowdate,
            "now_datetime": now_datetime,
            "__builtins__": {},
        }
        try:
            return eval(config["expression"], {"__builtins__": {}}, eval_context)
        except Exception:
            pass
    
    return default


# ============================================================================
# Additional Utility Transformers
# ============================================================================


@register_transformer("Concat")
def transform_concat(
    value: Any,
    config: dict,
    default: Any,
    source_data: dict,
    mapping: dict,
) -> Any:
    """
    Concatenate multiple fields or values.
    
    Config options:
        - fields: list[str] - Fields to concatenate
        - separator: str - Separator between values (default: " ")
        - prefix: str - Prefix string
        - suffix: str - Suffix string
    
    Example config:
        {
            "fields": ["first_name", "last_name"],
            "separator": " "
        }
    """
    fields = config.get("fields", [])
    separator = config.get("separator", " ")
    prefix = config.get("prefix", "")
    suffix = config.get("suffix", "")
    
    from ecomista.utils.field_mapper import FieldMapper
    mapper = FieldMapper()
    
    values = []
    for field in fields:
        field_value = mapper._get_nested_value(source_data, field)
        if field_value is not None and field_value != "":
            values.append(cstr(field_value))
    
    if not values:
        return default
    
    return prefix + separator.join(values) + suffix


@register_transformer("Split")
def transform_split(
    value: Any,
    config: dict,
    default: Any,
    source_data: dict,
    mapping: dict,
) -> Any:
    """
    Split a string and return specific part.
    
    Config options:
        - separator: str - Split separator (default: " ")
        - index: int - Index of part to return (default: 0)
        - join: bool - If true, return all parts as list
    
    Example config:
        {"separator": " ", "index": 0}  # Get first word
    """
    if value is None or value == "":
        return default
    
    separator = config.get("separator", " ")
    index = config.get("index", 0)
    
    parts = cstr(value).split(separator)
    
    if config.get("join"):
        return parts
    
    if 0 <= index < len(parts):
        return parts[index]
    
    return default


@register_transformer("Map")
def transform_map(
    value: Any,
    config: dict,
    default: Any,
    source_data: dict,
    mapping: dict,
) -> Any:
    """
    Map value using a mapping dictionary.
    
    Config options:
        - mapping: dict - Value mapping dictionary (required)
        - case_insensitive: bool - Case-insensitive matching
    
    Example config:
        {
            "mapping": {
                "pending": "Draft",
                "paid": "Paid",
                "refunded": "Cancelled"
            }
        }
    """
    if value is None:
        return default
    
    value_map = config.get("mapping", {})
    case_insensitive = config.get("case_insensitive", False)
    
    lookup_value = cstr(value)
    if case_insensitive:
        lookup_value = lookup_value.lower()
        value_map = {k.lower(): v for k, v in value_map.items()}
    
    return value_map.get(lookup_value, default)


@register_transformer("Regex")
def transform_regex(
    value: Any,
    config: dict,
    default: Any,
    source_data: dict,
    mapping: dict,
) -> Any:
    """
    Apply regex transformation.
    
    Config options:
        - pattern: str - Regex pattern (required)
        - replacement: str - Replacement string (for sub)
        - operation: str - "match", "search", "sub", "extract" (default: "extract")
        - group: int - Group to return for extract (default: 0)
    
    Example config:
        {"pattern": r"\\d+", "operation": "extract"}  # Extract first number
        {"pattern": r"[^a-zA-Z0-9]", "replacement": "", "operation": "sub"}  # Remove special chars
    """
    if value is None or value == "":
        return default
    
    pattern = config.get("pattern")
    if not pattern:
        return value
    
    operation = config.get("operation", "extract")
    str_value = cstr(value)
    
    try:
        if operation == "extract":
            match = re.search(pattern, str_value)
            if match:
                group = config.get("group", 0)
                return match.group(group)
            return default
        
        elif operation == "sub":
            replacement = config.get("replacement", "")
            return re.sub(pattern, replacement, str_value)
        
        elif operation == "match":
            return bool(re.match(pattern, str_value))
        
        elif operation == "search":
            return bool(re.search(pattern, str_value))
        
    except re.error as e:
        frappe.log_error(f"Regex transformer error: {e}\nPattern: {pattern}")
    
    return default


@register_transformer("Conditional")
def transform_conditional(
    value: Any,
    config: dict,
    default: Any,
    source_data: dict,
    mapping: dict,
) -> Any:
    """
    Conditional transformation based on conditions.
    
    Config options:
        - conditions: list[dict] - List of condition objects
            Each condition: {"if": "expression", "then": "value or expression"}
        - else: Any - Default value if no condition matches
        - eval_then: bool - If true, evaluate 'then' as expression (default: false)
    
    Example config:
        {
            "conditions": [
                {"if": "value > 100", "then": "High"},
                {"if": "value > 50", "then": "Medium"}
            ],
            "else": "Low"
        }
    """
    conditions = config.get("conditions", [])
    eval_then = config.get("eval_then", False)
    else_value = config.get("else", default)
    
    eval_context = {
        "value": value,
        "source": source_data,
        "flt": flt,
        "cint": cint,
        "cstr": cstr,
        "len": len,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
    }
    
    for condition in conditions:
        if_expr = condition.get("if", "")
        then_value = condition.get("then")
        
        try:
            if eval(if_expr, {"__builtins__": {}}, eval_context):
                if eval_then and isinstance(then_value, str):
                    return eval(then_value, {"__builtins__": {}}, eval_context)
                return then_value
        except Exception:
            continue
    
    return else_value
