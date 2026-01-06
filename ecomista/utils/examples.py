# Copyright (c) 2026, Shaqwieer and contributors
# For license information, please see license.txt

"""
Examples Module - Demonstrates Field Mapping Usage

This module provides example data and mappings to demonstrate
how the field mapper works with real-world scenarios like Shopify.
"""

from ecomista.utils.field_mapper import FieldMapper, map_data


# ============================================================================
# Example: Shopify Order to ERPNext Sales Invoice
# ============================================================================

SHOPIFY_ORDER_EXAMPLE = {
    "id": 5678901234,
    "order_number": "1001",
    "name": "#1001",
    "email": "john.doe@example.com",
    "created_at": "2026-01-06T10:30:00-05:00",
    "updated_at": "2026-01-06T10:35:00-05:00",
    "financial_status": "paid",
    "fulfillment_status": "unfulfilled",
    "currency": "USD",
    "total_price": "149.99",
    "subtotal_price": "139.99",
    "total_tax": "10.00",
    "total_discounts": "15.00",
    "total_shipping_price_set": {
        "shop_money": {
            "amount": "10.00",
            "currency_code": "USD"
        }
    },
    "customer": {
        "id": 1234567890,
        "email": "john.doe@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+1-555-123-4567",
        "default_address": {
            "address1": "123 Main Street",
            "address2": "Apt 4B",
            "city": "New York",
            "province": "NY",
            "province_code": "NY",
            "country": "United States",
            "country_code": "US",
            "zip": "10001"
        }
    },
    "billing_address": {
        "first_name": "John",
        "last_name": "Doe",
        "address1": "123 Main Street",
        "address2": "Apt 4B",
        "city": "New York",
        "province": "New York",
        "province_code": "NY",
        "country": "United States",
        "country_code": "US",
        "zip": "10001",
        "phone": "+1-555-123-4567"
    },
    "shipping_address": {
        "first_name": "John",
        "last_name": "Doe",
        "address1": "456 Oak Avenue",
        "address2": "",
        "city": "Brooklyn",
        "province": "New York",
        "province_code": "NY",
        "country": "United States",
        "country_code": "US",
        "zip": "11201",
        "phone": "+1-555-987-6543"
    },
    "line_items": [
        {
            "id": 111111,
            "variant_id": 222222,
            "product_id": 333333,
            "title": "Premium Widget",
            "name": "Premium Widget - Blue / Large",
            "sku": "WIDGET-BLU-LG",
            "quantity": 2,
            "price": "49.99",
            "total_discount": "10.00",
            "taxable": True,
            "tax_lines": [
                {"title": "State Tax", "rate": 0.08, "price": "8.00"}
            ],
            "properties": [],
            "vendor": "WidgetCo",
            "grams": 500
        },
        {
            "id": 444444,
            "variant_id": 555555,
            "product_id": 666666,
            "title": "Widget Accessory",
            "name": "Widget Accessory - Standard",
            "sku": "WIDGET-ACC-STD",
            "quantity": 1,
            "price": "39.99",
            "total_discount": "5.00",
            "taxable": True,
            "tax_lines": [
                {"title": "State Tax", "rate": 0.08, "price": "2.00"}
            ],
            "properties": [],
            "vendor": "WidgetCo",
            "grams": 200
        }
    ],
    "shipping_lines": [
        {
            "id": 777777,
            "title": "Standard Shipping",
            "price": "10.00",
            "code": "STANDARD"
        }
    ],
    "discount_codes": [
        {
            "code": "SAVE15",
            "amount": "15.00",
            "type": "fixed_amount"
        }
    ],
    "note": "Please leave at the door",
    "tags": "vip, repeat-customer",
    "payment_gateway_names": ["shopify_payments"],
    "processing_method": "direct"
}


# Field mappings for Shopify Order -> ERPNext Sales Invoice
SHOPIFY_TO_INVOICE_MAPPINGS = [
    # ========== Header Fields ==========
    {
        "source_field": "order_number",
        "target_field": "po_no",
        "transformation": "Direct",
        "transform_config": None,
        "default_value": None,
        "is_child_mapping": False,
        "child_source_path": None,
        "child_target_path": None,
    },
    {
        "source_field": "name",
        "target_field": "shopify_order_id",
        "transformation": "Direct",
        "transform_config": None,
        "default_value": None,
        "is_child_mapping": False,
        "child_source_path": None,
        "child_target_path": None,
    },
    {
        "source_field": "customer.email",
        "target_field": "customer",
        "transformation": "Lookup",
        "transform_config": '{"doctype": "Customer", "match_field": "email_id", "return_field": "name", "create_if_missing": false}',
        "default_value": "Guest Customer",
        "is_child_mapping": False,
        "child_source_path": None,
        "child_target_path": None,
    },
    {
        "source_field": "customer.first_name",
        "target_field": "customer_name",
        "transformation": "Concat",
        "transform_config": '{"fields": ["customer.first_name", "customer.last_name"], "separator": " "}',
        "default_value": "Unknown Customer",
        "is_child_mapping": False,
        "child_source_path": None,
        "child_target_path": None,
    },
    {
        "source_field": "created_at",
        "target_field": "posting_date",
        "transformation": "Cast",
        "transform_config": '{"type": "date"}',
        "default_value": None,
        "is_child_mapping": False,
        "child_source_path": None,
        "child_target_path": None,
    },
    {
        "source_field": "currency",
        "target_field": "currency",
        "transformation": "Direct",
        "transform_config": None,
        "default_value": "USD",
        "is_child_mapping": False,
        "child_source_path": None,
        "child_target_path": None,
    },
    {
        "source_field": "financial_status",
        "target_field": "status",
        "transformation": "Map",
        "transform_config": '{"mapping": {"pending": "Draft", "paid": "Paid", "partially_paid": "Partly Paid", "refunded": "Cancelled", "voided": "Cancelled"}, "case_insensitive": true}',
        "default_value": "Draft",
        "is_child_mapping": False,
        "child_source_path": None,
        "child_target_path": None,
    },
    {
        "source_field": "total_price",
        "target_field": "grand_total",
        "transformation": "Cast",
        "transform_config": '{"type": "float"}',
        "default_value": "0",
        "is_child_mapping": False,
        "child_source_path": None,
        "child_target_path": None,
    },
    {
        "source_field": "subtotal_price",
        "target_field": "net_total",
        "transformation": "Cast",
        "transform_config": '{"type": "float"}',
        "default_value": "0",
        "is_child_mapping": False,
        "child_source_path": None,
        "child_target_path": None,
    },
    {
        "source_field": "total_tax",
        "target_field": "total_taxes_and_charges",
        "transformation": "Cast",
        "transform_config": '{"type": "float"}',
        "default_value": "0",
        "is_child_mapping": False,
        "child_source_path": None,
        "child_target_path": None,
    },
    {
        "source_field": "total_discounts",
        "target_field": "discount_amount",
        "transformation": "Cast",
        "transform_config": '{"type": "float"}',
        "default_value": "0",
        "is_child_mapping": False,
        "child_source_path": None,
        "child_target_path": None,
    },
    {
        "source_field": "note",
        "target_field": "remarks",
        "transformation": "Direct",
        "transform_config": None,
        "default_value": None,
        "is_child_mapping": False,
        "child_source_path": None,
        "child_target_path": None,
    },
    # ========== Billing Address ==========
    {
        "source_field": "billing_address.address1",
        "target_field": "customer_address",
        "transformation": "Concat",
        "transform_config": '{"fields": ["billing_address.address1", "billing_address.address2", "billing_address.city", "billing_address.province", "billing_address.zip"], "separator": ", "}',
        "default_value": None,
        "is_child_mapping": False,
        "child_source_path": None,
        "child_target_path": None,
    },
    {
        "source_field": "billing_address.phone",
        "target_field": "contact_mobile",
        "transformation": "Regex",
        "transform_config": '{"pattern": "[^0-9+]", "operation": "sub", "replacement": ""}',
        "default_value": None,
        "is_child_mapping": False,
        "child_source_path": None,
        "child_target_path": None,
    },
    # ========== Shipping Address ==========
    {
        "source_field": "shipping_address.address1",
        "target_field": "shipping_address_name",
        "transformation": "Concat",
        "transform_config": '{"fields": ["shipping_address.address1", "shipping_address.city", "shipping_address.province", "shipping_address.zip"], "separator": ", "}',
        "default_value": None,
        "is_child_mapping": False,
        "child_source_path": None,
        "child_target_path": None,
    },
    # ========== Line Items (Child Table) ==========
    {
        "source_field": "sku",
        "target_field": "item_code",
        "transformation": "Lookup",
        "transform_config": '{"doctype": "Item", "match_field": "item_code", "return_field": "name"}',
        "default_value": None,
        "is_child_mapping": True,
        "child_source_path": "line_items",
        "child_target_path": "items",
    },
    {
        "source_field": "title",
        "target_field": "item_name",
        "transformation": "Direct",
        "transform_config": None,
        "default_value": "Unknown Item",
        "is_child_mapping": True,
        "child_source_path": "line_items",
        "child_target_path": "items",
    },
    {
        "source_field": "name",
        "target_field": "description",
        "transformation": "Direct",
        "transform_config": None,
        "default_value": None,
        "is_child_mapping": True,
        "child_source_path": "line_items",
        "child_target_path": "items",
    },
    {
        "source_field": "quantity",
        "target_field": "qty",
        "transformation": "Cast",
        "transform_config": '{"type": "int"}',
        "default_value": "1",
        "is_child_mapping": True,
        "child_source_path": "line_items",
        "child_target_path": "items",
    },
    {
        "source_field": "price",
        "target_field": "rate",
        "transformation": "Cast",
        "transform_config": '{"type": "float"}',
        "default_value": "0",
        "is_child_mapping": True,
        "child_source_path": "line_items",
        "child_target_path": "items",
    },
    {
        "source_field": "price",
        "target_field": "amount",
        "transformation": "Formula",
        "transform_config": '{"expression": "flt(value) * source.get(\\"quantity\\", 1)"}',
        "default_value": "0",
        "is_child_mapping": True,
        "child_source_path": "line_items",
        "child_target_path": "items",
    },
    {
        "source_field": "total_discount",
        "target_field": "discount_amount",
        "transformation": "Cast",
        "transform_config": '{"type": "float"}',
        "default_value": "0",
        "is_child_mapping": True,
        "child_source_path": "line_items",
        "child_target_path": "items",
    },
    {
        "source_field": "grams",
        "target_field": "weight_per_unit",
        "transformation": "Formula",
        "transform_config": '{"expression": "flt(value) / 1000"}',
        "default_value": "0",
        "is_child_mapping": True,
        "child_source_path": "line_items",
        "child_target_path": "items",
    },
]


def run_shopify_example() -> dict:
    """
    Run the Shopify to Invoice mapping example.
    
    Returns:
        Mapped invoice data dictionary
    """
    # Create mapper with the mappings
    mapper = FieldMapper(mappings=SHOPIFY_TO_INVOICE_MAPPINGS)
    
    # Transform the Shopify order
    result = mapper.transform(SHOPIFY_ORDER_EXAMPLE)
    
    return result


def get_expected_result() -> dict:
    """
    Get the expected result of the Shopify mapping.
    
    This shows what the output should look like after transformation.
    """
    return {
        "po_no": "1001",
        "shopify_order_id": "#1001",
        "customer": "Guest Customer",  # Lookup would return actual customer if exists
        "customer_name": "John Doe",
        "posting_date": "2026-01-06",
        "currency": "USD",
        "status": "Paid",
        "grand_total": 149.99,
        "net_total": 139.99,
        "total_taxes_and_charges": 10.0,
        "discount_amount": 15.0,
        "remarks": "Please leave at the door",
        "customer_address": "123 Main Street, Apt 4B, New York, New York, 10001",
        "contact_mobile": "+15551234567",
        "shipping_address_name": "456 Oak Avenue, Brooklyn, New York, 11201",
        "items": [
            {
                "item_code": None,  # Lookup would return actual item if exists
                "item_name": "Premium Widget",
                "description": "Premium Widget - Blue / Large",
                "qty": 2,
                "rate": 49.99,
                "amount": 99.98,
                "discount_amount": 10.0,
                "weight_per_unit": 0.5,
            },
            {
                "item_code": None,  # Lookup would return actual item if exists
                "item_name": "Widget Accessory",
                "description": "Widget Accessory - Standard",
                "qty": 1,
                "rate": 39.99,
                "amount": 39.99,
                "discount_amount": 5.0,
                "weight_per_unit": 0.2,
            },
        ],
    }


def print_example_output():
    """Print a formatted example of the mapping transformation."""
    import json
    
    print("=" * 80)
    print("SHOPIFY ORDER TO ERPNEXT INVOICE MAPPING EXAMPLE")
    print("=" * 80)
    
    print("\n📥 SOURCE (Shopify Order):")
    print("-" * 40)
    print(json.dumps(SHOPIFY_ORDER_EXAMPLE, indent=2)[:2000] + "...\n")
    
    print("\n📤 RESULT (ERPNext Invoice):")
    print("-" * 40)
    result = run_shopify_example()
    print(json.dumps(result, indent=2, default=str))
    
    print("\n" + "=" * 80)
    print("MAPPING SUMMARY")
    print("=" * 80)
    print(f"Total mappings: {len(SHOPIFY_TO_INVOICE_MAPPINGS)}")
    print(f"Header fields: {sum(1 for m in SHOPIFY_TO_INVOICE_MAPPINGS if not m['is_child_mapping'])}")
    print(f"Line item fields: {sum(1 for m in SHOPIFY_TO_INVOICE_MAPPINGS if m['is_child_mapping'])}")
    
    transformations = {}
    for m in SHOPIFY_TO_INVOICE_MAPPINGS:
        t = m["transformation"]
        transformations[t] = transformations.get(t, 0) + 1
    
    print("\nTransformations used:")
    for t, count in sorted(transformations.items()):
        print(f"  - {t}: {count}")


# ============================================================================
# Example: Customer Sync (Shopify -> ERPNext)
# ============================================================================

SHOPIFY_CUSTOMER_EXAMPLE = {
    "id": 9876543210,
    "email": "jane.smith@example.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "phone": "+1-555-999-8888",
    "verified_email": True,
    "tax_exempt": False,
    "created_at": "2025-06-15T14:20:00-05:00",
    "updated_at": "2026-01-05T09:15:00-05:00",
    "orders_count": 5,
    "total_spent": "549.95",
    "currency": "USD",
    "tags": "wholesale, verified",
    "note": "Preferred customer, qualifies for bulk discounts",
    "default_address": {
        "id": 111222333,
        "address1": "789 Business Park",
        "address2": "Suite 100",
        "city": "San Francisco",
        "province": "California",
        "province_code": "CA",
        "country": "United States",
        "country_code": "US",
        "zip": "94102",
        "phone": "+1-555-999-8888",
        "company": "Smith Industries"
    }
}


SHOPIFY_TO_CUSTOMER_MAPPINGS = [
    {
        "source_field": "id",
        "target_field": "shopify_customer_id",
        "transformation": "Cast",
        "transform_config": '{"type": "string"}',
        "default_value": None,
        "is_child_mapping": False,
        "child_source_path": None,
        "child_target_path": None,
    },
    {
        "source_field": "email",
        "target_field": "email_id",
        "transformation": "Direct",
        "transform_config": '{"lower": true}',
        "default_value": None,
        "is_child_mapping": False,
        "child_source_path": None,
        "child_target_path": None,
    },
    {
        "source_field": "first_name",
        "target_field": "customer_name",
        "transformation": "Concat",
        "transform_config": '{"fields": ["first_name", "last_name"], "separator": " "}',
        "default_value": None,
        "is_child_mapping": False,
        "child_source_path": None,
        "child_target_path": None,
    },
    {
        "source_field": "phone",
        "target_field": "mobile_no",
        "transformation": "Regex",
        "transform_config": '{"pattern": "[^0-9+]", "operation": "sub", "replacement": ""}',
        "default_value": None,
        "is_child_mapping": False,
        "child_source_path": None,
        "child_target_path": None,
    },
    {
        "source_field": "default_address.company",
        "target_field": "company_name",
        "transformation": "Direct",
        "transform_config": None,
        "default_value": None,
        "is_child_mapping": False,
        "child_source_path": None,
        "child_target_path": None,
    },
    {
        "source_field": "tags",
        "target_field": "customer_group",
        "transformation": "Conditional",
        "transform_config": '{"conditions": [{"if": "\\"wholesale\\" in str(value).lower()", "then": "Wholesale"}, {"if": "\\"retail\\" in str(value).lower()", "then": "Retail"}], "else": "Individual"}',
        "default_value": "Individual",
        "is_child_mapping": False,
        "child_source_path": None,
        "child_target_path": None,
    },
    {
        "source_field": "tax_exempt",
        "target_field": "is_tax_exempt",
        "transformation": "Cast",
        "transform_config": '{"type": "bool"}',
        "default_value": "0",
        "is_child_mapping": False,
        "child_source_path": None,
        "child_target_path": None,
    },
    {
        "source_field": "total_spent",
        "target_field": "lifetime_value",
        "transformation": "Cast",
        "transform_config": '{"type": "float"}',
        "default_value": "0",
        "is_child_mapping": False,
        "child_source_path": None,
        "child_target_path": None,
    },
    {
        "source_field": "note",
        "target_field": "customer_details",
        "transformation": "Direct",
        "transform_config": None,
        "default_value": None,
        "is_child_mapping": False,
        "child_source_path": None,
        "child_target_path": None,
    },
    {
        "source_field": "default_address.address1",
        "target_field": "primary_address",
        "transformation": "Concat",
        "transform_config": '{"fields": ["default_address.address1", "default_address.address2", "default_address.city", "default_address.province", "default_address.zip", "default_address.country"], "separator": ", "}',
        "default_value": None,
        "is_child_mapping": False,
        "child_source_path": None,
        "child_target_path": None,
    },
]


def run_customer_example() -> dict:
    """Run the Shopify Customer mapping example."""
    mapper = FieldMapper(mappings=SHOPIFY_TO_CUSTOMER_MAPPINGS)
    return mapper.transform(SHOPIFY_CUSTOMER_EXAMPLE)
