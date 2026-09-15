package com.goodgrocer.app

import com.goodgrocer.app.data.Address
import com.goodgrocer.app.data.CartLine
import com.goodgrocer.app.data.ProductPage
import com.goodgrocer.app.data.updateQuantity
import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Test

class ContractTest {
    private val moshi = Moshi.Builder().addLast(KotlinJsonAdapterFactory()).build()
    private val catalogue = """
        {"items":[{"id":1,"name":"Tomatoes","description":"Fresh","image_url":null,
        "active":true,"available":true,"brand":{"id":1,"name":"Farm"},"categories":[],
        "variants":[{"id":2,"product_id":1,"name":"500 g","mrp":"30.00",
        "selling_price":"24.00","active":true,"available":true}]}],
        "total":1,"page":1,"page_size":24}
    """.trimIndent()

    @Test
    fun catalogueDecimalStringsDecodeAndCartRoundTrips() {
        val product = moshi.adapter(ProductPage::class.java).fromJson(catalogue)!!.items.single()
        val line = CartLine(product, product.variants.single(), 2)
        val adapter = moshi.adapter(CartLine::class.java)
        assertEquals(line, adapter.fromJson(adapter.toJson(line)))
        assertEquals("24.00", line.variant.selling_price)
    }

    @Test
    fun addressWritesOmitReadOnlyId() {
        val address = Address(id = 7, recipient_name = "Sam", phone = "+919876543210")
        val json = moshi.adapter(Address::class.java).toJson(address.copy(id = null))
        assertFalse(json.contains("\"id\""))
    }

    @Test
    fun updatingQuantityPreservesBasketOrder() {
        val product = moshi.adapter(ProductPage::class.java).fromJson(catalogue)!!.items.single()
        val first = product.variants.single()
        val second = first.copy(id = 3)
        val lines = listOf(CartLine(product, first, 1), CartLine(product, second, 1))
        val updated = updateQuantity(lines, product, first, 2)
        assertEquals(listOf(first.id, second.id), updated.map { it.variant.id })
        assertEquals(2, updated.first().quantity)
    }
}
