package com.goodgrocer.app

import com.goodgrocer.app.data.Brand
import com.goodgrocer.app.data.CartLine
import com.goodgrocer.app.data.Product
import com.goodgrocer.app.data.Variant
import com.goodgrocer.app.data.cartSubtotal
import com.goodgrocer.app.data.updateQuantity
import java.math.BigDecimal
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class CartTest {
    private val variant = Variant(1, 1, "1 kg", "120.00", "100.25")
    private val product =
        Product(1, "Rice", "", null, true, true, Brand(1, "Farm"), emptyList(), listOf(variant))

    @Test fun subtotalUsesDecimalAndQuantity() {
        assertEquals(BigDecimal("200.50"), cartSubtotal(listOf(CartLine(product, variant, 2))))
    }

    @Test fun quantityReplacesWithoutDuplicatesAndZeroRemoves() {
        val initial = updateQuantity(emptyList(), product, variant, 1)
        val updated = updateQuantity(initial, product, variant, 3)
        assertEquals(1, updated.size)
        assertEquals(3, updated.single().quantity)
        assertTrue(updateQuantity(updated, product, variant, 0).isEmpty())
    }

    @Test fun quantityIsBounded() {
        assertEquals(99, updateQuantity(emptyList(), product, variant, 100).single().quantity)
    }
}
