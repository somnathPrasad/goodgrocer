package com.goodgrocer.app.data

import java.math.BigDecimal

data class Brand(val id: Int, val name: String)
data class Category(val id: Int, val name: String, val image_url: String? = null)
data class Variant(
    val id: Int,
    val product_id: Int,
    val name: String,
    val mrp: String,
    val selling_price: String,
    val active: Boolean = true,
    val available: Boolean = true
)
data class Product(
    val id: Int,
    val name: String,
    val description: String,
    val image_url: String?,
    val active: Boolean,
    val available: Boolean,
    val brand: Brand,
    val categories: List<Category>,
    val variants: List<Variant>
)
data class ProductPage(val items: List<Product>, val total: Int, val page: Int, val page_size: Int)
data class CartLine(val product: Product, val variant: Variant, val quantity: Int)
data class CartItem(val variant_id: Int, val quantity: Int)
data class GoogleLoginRequest(val id_token: String)
data class AuthToken(val token: String, val expires_at: String)
data class Address(
    val id: Int? = null,
    val recipient_name: String = "",
    val phone: String = "",
    val line1: String = "",
    val line2: String? = null,
    val landmark: String? = null,
    val locality: String? = null,
    val city: String = "",
    val state: String = "",
    val postal_code: String? = null
)
data class CheckoutRequest(
    val items: List<CartItem>,
    val fulfilment_type: String,
    val payment_method: String,
    val address_id: Int? = null,
    val contact_phone: String? = null
)
data class OrderRequest(
    val items: List<CartItem>,
    val fulfilment_type: String,
    val payment_method: String,
    val address_id: Int?,
    val quote_token: String,
    val idempotency_key: String,
    val contact_phone: String? = null
)
data class Quote(
    val items: List<OrderItem>,
    val subtotal: String,
    val delivery_fee: String,
    val discount: String,
    val total: String,
    val quote_token: String
)
data class OrderItem(
    val product_id: Int,
    val variant_id: Int,
    val product_name: String,
    val variant_name: String,
    val quantity: Int,
    val unit_mrp: String,
    val unit_selling_price: String,
    val line_total: String
)
data class Order(
    val id: Int,
    val order_number: String,
    val fulfilment_type: String,
    val status: String,
    val payment_method: String,
    val payment_status: String,
    val subtotal: String,
    val delivery_fee: String,
    val total: String,
    val created_at: String,
    val items: List<OrderItem>,
    val address_snapshot: Address?,
    val cancellation_reason: String?
)
data class ReorderResult(
    val items: List<CartItem>,
    val products: List<Product>,
    val unavailable: List<String>
)
data class StoreConfig(
    val online_upi_enabled: Boolean,
    val development: Boolean,
    val delivery_fee: String
)

fun cartSubtotal(lines: List<CartLine>): BigDecimal = lines.fold(BigDecimal.ZERO) { sum, item ->
    sum +
        item.variant.selling_price.toBigDecimal() * item.quantity.toBigDecimal()
}
fun updateQuantity(
    lines: List<CartLine>,
    product: Product,
    variant: Variant,
    quantity: Int
): List<CartLine> {
    if (quantity <= 0) return lines.filterNot { it.variant.id == variant.id }
    val updated = CartLine(product, variant, quantity.coerceAtMost(99))
    return if (lines.any { it.variant.id == variant.id }) {
        lines.map { if (it.variant.id == variant.id) updated else it }
    } else {
        lines + updated
    }
}
