package com.goodgrocer.app.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.FilterChip
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedCard
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.goodgrocer.app.data.CartLine
import kotlinx.coroutines.delay

@Composable
fun CheckoutScreen(
    vm: ShopViewModel,
    cart: List<CartLine>,
    addresses: () -> Unit,
    placed: (Int) -> Unit
) {
    val state = collectShopState(vm)
    LaunchedEffect(Unit) { vm.loadAddresses() }
    LazyColumn(
        contentPadding = PaddingValues(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        item {
            // Keep the other option defined for a later release.
            val fulfilmentOptions = listOf(
                "DELIVERY" to "Delivery",
                "PICKUP" to "Store pickup"
            ).filter { (value, _) -> value == "DELIVERY" }
            SectionTitle(
                if (fulfilmentOptions.size == 1) {
                    "Delivery order"
                } else {
                    "How would you like your order?"
                }
            )
            if (fulfilmentOptions.size > 1) {
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    fulfilmentOptions.forEach { (value, label) ->
                        FilterChip(
                            selected = state.fulfilment == value,
                            onClick = { vm.checkoutOptions(fulfilment = value) },
                            label = { Text(label) }
                        )
                    }
                }
            }
        }
        if (state.fulfilment == "DELIVERY") {
            item {
                SectionTitle(
                    "Delivery address",
                    "Your store will confirm whether it can serve this address."
                )
            }
            items(state.addresses, key = { it.id!! }) { address ->
                OutlinedCard(onClick = { vm.checkoutOptions(addressId = address.id) }) {
                    Row(
                        Modifier.fillMaxWidth().padding(12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        RadioButton(
                            selected =
                            state.addressId == address.id,
                            onClick = {
                                vm.checkoutOptions(addressId = address.id)
                            }
                        )
                        Column {
                            Text(address.recipient_name, fontWeight = FontWeight.Bold)
                            Text(
                                "${address.line1}, ${address.city}",
                                style = MaterialTheme.typography.bodyMedium
                            )
                        }
                    }
                }
            }
            item {
                OutlinedButton(onClick = addresses) {
                    Text(
                        if (state.addresses.isEmpty()) {
                            "Add delivery address"
                        } else {
                            "Manage addresses"
                        }
                    )
                }
            }
        } else {
            item {
                Text(
                    "Collect your order from the store after it is accepted. Show your order number when you arrive."
                )
                ShopField(
                    "Contact phone for pickup",
                    state.contactPhone,
                    { vm.checkoutOptions(contactPhone = it) },
                    keyboard = KeyboardOptions(keyboardType = KeyboardType.Phone)
                )
            }
        }
        item {
            SectionTitle("Payment")
            // Keep the other methods defined for a later release.
            val paymentOptions = listOf(
                "COD" to "Cash on delivery",
                "UPI_ON_DELIVERY" to "UPI on delivery / collection",
                "ONLINE_UPI" to "Online UPI"
            ).filter { (value, _) -> value == "COD" }
            if (paymentOptions.size == 1) {
                Text(paymentOptions.single().second)
            } else {
                paymentOptions.forEach { (value, label) ->
                    val enabled = value == "COD"
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        RadioButton(
                            selected =
                            state.payment == value,
                            onClick = {
                                vm.checkoutOptions(payment = value)
                            },
                            enabled = enabled
                        )
                        Column {
                            Text(label)
                            if (!enabled) {
                                Text(
                                    "Not available yet",
                                    style = MaterialTheme.typography.bodySmall
                                )
                            }
                            if (value ==
                                "ONLINE_UPI" &&
                                enabled &&
                                state.config?.development == true
                            ) {
                                Text(
                                    "Development test payment",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = Forest
                                )
                            }
                        }
                    }
                }
            }
        }
        item {
            val quote = state.quote
            if (quote != null) {
                SectionTitle("Your confirmed total")
                quote.items.forEach { item ->
                    Row(
                        Modifier.fillMaxWidth().padding(vertical = 6.dp),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(
                            "${item.quantity} × ${item.product_name}\n${item.variant_name}",
                            Modifier.weight(1f)
                        )
                        Text(rupees(item.line_total))
                    }
                }
                HorizontalDivider(Modifier.padding(vertical = 12.dp))
                TotalRow("Subtotal", quote.subtotal)
                TotalRow("Delivery", quote.delivery_fee)
                TotalRow("Total", quote.total, true)
                Spacer(Modifier.height(16.dp))
                PrimaryButton(
                    if (state.actionLoading) {
                        "Placing order…"
                    } else {
                        "Place order · ${rupees(
                            quote.total
                        )}"
                    },
                    !state.actionLoading && cart.isNotEmpty()
                ) { vm.placeOrder(placed) }
            } else {
                Text(
                    "We’ll check current prices and availability before you place the order.",
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(Modifier.height(16.dp))
                PrimaryButton(
                    if (state.actionLoading) "Checking…" else "Review final total",
                    !state.actionLoading &&
                        cart.isNotEmpty() &&
                        (
                            state.fulfilment == "PICKUP" &&
                                state.contactPhone.length >= 10 ||
                                state.fulfilment == "DELIVERY" &&
                                state.addressId != null
                            )
                ) {
                    vm.reviewQuote()
                }
            }
        }
    }
}

@Composable
fun TotalRow(label: String, amount: String, bold: Boolean = false) {
    Row(
        Modifier.fillMaxWidth().padding(vertical = 6.dp),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(label, fontWeight = if (bold) FontWeight.Bold else FontWeight.Normal)
        Text(rupees(amount), fontWeight = if (bold) FontWeight.Bold else FontWeight.Normal)
    }
}

@Composable
fun OrdersScreen(vm: ShopViewModel, open: (Int) -> Unit) {
    val state = collectShopState(vm)
    LaunchedEffect(Unit) { vm.loadOrders() }
    if (state.ordersLoading && state.orders.isEmpty()) {
        LoadingState()
        return
    }
    if (state.orders.isEmpty()) {
        EmptyState(
            "Your first order starts here",
            "Placed orders will appear here, ready to track or reorder.",
            "Refresh",
            {
                vm.loadOrders()
            }
        )
        return
    }
    LazyColumn(
        contentPadding = PaddingValues(20.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        items(state.orders, key = { it.id }) { order ->
            Card(
                onClick = {
                    open(order.id)
                },
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surface
                )
            ) {
                Column(
                    Modifier.fillMaxWidth().padding(18.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text(order.order_number, fontWeight = FontWeight.Bold)
                        Text(rupees(order.total), fontWeight = FontWeight.Bold)
                    }
                    Text(
                        order.status.replace('_', ' '),
                        color = Forest,
                        style = MaterialTheme.typography.labelLarge
                    )
                    Text(
                        order.items.joinToString {
                            "${it.product_name} × ${it.quantity}"
                        },
                        maxLines = 2
                    )
                    Text(
                        order.created_at.take(10) + " · " + order.fulfilment_type,
                        style = MaterialTheme.typography.bodySmall
                    )
                }
            }
        }
        if (state.moreOrders) {
            item {
                PrimaryButton("Load older orders", !state.ordersLoading) { vm.loadOrders(true) }
            }
        }
    }
}

@Composable
fun OrderScreen(id: Int, success: Boolean, vm: ShopViewModel, reordered: () -> Unit) {
    val state = collectShopState(vm)
    LaunchedEffect(id) {
        vm.loadOrder(id)
        while (true) {
            delay(15000)
            vm.loadOrder(id, true)
        }
    }
    var confirmReorder by remember { mutableStateOf(false) }
    val order = state.order?.takeIf { it.id == id }
    if (order ==
        null
    ) {
        if (state.orderLoading) {
            LoadingState()
        } else {
            EmptyState("Couldn’t load this order", "Please try again.", "Retry", {
                vm.loadOrder(id)
            })
        }
        return
    }
    LazyColumn(
        contentPadding = PaddingValues(24.dp),
        verticalArrangement = Arrangement.spacedBy(18.dp)
    ) {
        item {
            if (success) {
                Text(
                    "Thank you.\nWe’ve got your order.",
                    style = MaterialTheme.typography.headlineLarge
                )
                Spacer(Modifier.height(14.dp))
            }
            SectionTitle(order.order_number, order.created_at.take(10))
            Text(
                order.fulfilment_type.replace('_', ' ') + " · " +
                    order.payment_method.replace('_', ' ')
            )
            Text("Payment: ${order.payment_status}")
        }
        item {
            if (order.status ==
                "CANCELLED"
            ) {
                Card(
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.errorContainer
                    )
                ) {
                    Column(Modifier.padding(18.dp)) {
                        Text("Order cancelled", fontWeight = FontWeight.Bold)
                        Text(
                            order.cancellation_reason ?: "Contact the store for details"
                        )
                    }
                }
            } else {
                val stages = if (order.fulfilment_type ==
                    "PICKUP"
                ) {
                    listOf("PLACED", "ACCEPTED", "DELIVERED")
                } else {
                    listOf("PLACED", "ACCEPTED", "OUT_FOR_DELIVERY", "DELIVERED")
                }
                stages.forEachIndexed { index, value ->
                    Row(
                        Modifier.padding(vertical = 8.dp),
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Text(
                            if (index <=
                                stages.indexOf(order.status)
                            ) {
                                "●"
                            } else {
                                "○"
                            },
                            color = Forest
                        )
                        Text(
                            if (value ==
                                "DELIVERED" &&
                                order.fulfilment_type == "PICKUP"
                            ) {
                                "Collected"
                            } else {
                                value.lowercase().replace('_', ' ').replaceFirstChar {
                                    it.uppercase()
                                }
                            },
                            fontWeight = if (value ==
                                order.status
                            ) {
                                FontWeight.Bold
                            } else {
                                FontWeight.Normal
                            }
                        )
                    }
                }
            }
            TextButton(onClick = { vm.loadOrder(id, true) }) { Text("Refresh status") }
        }
        if (order.payment_method == "ONLINE_UPI" &&
            order.payment_status == "PENDING" &&
            order.status == "PLACED" &&
            state.config?.development == true
        ) {
            item {
                SectionTitle(
                    "Development payment",
                    "No money is transferred. Choose an outcome to test checkout."
                )
                PrimaryButton("Simulate successful payment", !state.actionLoading) {
                    vm.developmentPayment(id, "PAID")
                }
                TextButton(onClick = {
                    vm.developmentPayment(id, "FAILED")
                }, enabled = !state.actionLoading) { Text("Simulate failed payment") }
            }
        }
        items(order.items, key = {
            it.variant_id
        }) { item ->
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Column(Modifier.weight(1f)) {
                    Text(item.product_name, fontWeight = FontWeight.Bold)
                    Text(
                        "${item.variant_name} × ${item.quantity}",
                        style = MaterialTheme.typography.bodySmall
                    )
                }
                Text(rupees(item.line_total))
            }
        }
        item {
            HorizontalDivider()
            TotalRow("Subtotal", order.subtotal)
            TotalRow("Delivery", order.delivery_fee)
            TotalRow("Total", order.total, true)
        }
        order.address_snapshot?.let { address ->
            item {
                SectionTitle("Deliver to")
                Text(
                    "${address.recipient_name}\n${address.line1}\n${address.city}, ${address.state}\n${address.phone}"
                )
            }
        }
        item {
            PrimaryButton("Reorder with today’s prices", !state.actionLoading) {
                confirmReorder =
                    true
            }
        }
    }
    if (confirmReorder) {
        AlertDialog(onDismissRequest = {
            confirmReorder = false
        }, title = {
            Text("Start a new basket?")
        }, text = {
            Text(
                "This replaces your current basket. We’ll use today’s prices and tell you which items are unavailable."
            )
        }, confirmButton = {
            TextButton(onClick = {
                confirmReorder =
                    false
                vm.reorder(id, reordered)
            }) { Text("Reorder") }
        }, dismissButton = {
            TextButton(onClick = {
                confirmReorder =
                    false
            }) { Text("Keep basket") }
        })
    }
}
