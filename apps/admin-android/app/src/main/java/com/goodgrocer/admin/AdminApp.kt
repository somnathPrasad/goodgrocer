package com.goodgrocer.admin

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Checkbox
import androidx.compose.material3.FilterChip
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import java.math.BigDecimal
import java.text.NumberFormat
import java.util.Locale

private val sections = listOf("Dashboard", "Orders", "Products", "Categories", "Brands")
private val orderStatuses = listOf("PLACED", "ACCEPTED", "OUT_FOR_DELIVERY", "DELIVERED", "CANCELLED")
private fun money(value: String) = runCatching { NumberFormat.getCurrencyInstance(Locale.forLanguageTag("en-IN")).format(BigDecimal(value)) }.getOrDefault(value)
private fun slug(name: String) = name.lowercase(Locale.ROOT).replace(Regex("[^a-z0-9]+"), "-").trim('-')

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AdminApp(vm: AdminViewModel) {
    val s by vm.state.collectAsState()
    if (s.signedIn == null) { Text("Opening store desk…", Modifier.padding(24.dp)); return }
    if (s.signedIn == false) { LoginScreen(s, vm); return }
    var editBrand by remember { mutableStateOf<Brand?>(null) }
    var editCategory by remember { mutableStateOf<Category?>(null) }
    var addingBrand by remember { mutableStateOf(false) }
    var addingCategory by remember { mutableStateOf(false) }
    var addingProduct by remember { mutableStateOf(false) }
    if (s.selectedOrder != null) {
        OrderScreen(s.selectedOrder!!, s.busy, s.error, vm)
        return
    }
    if (s.selectedProduct != null || addingProduct) {
        ProductEditor(s.selectedProduct, s, vm) { vm.closeProduct(); addingProduct = false }
        return
    }
    if (editBrand != null || addingBrand) {
        BrandEditor(editBrand, s.busy, s.error, vm) { editBrand = null; addingBrand = false }
        return
    }
    if (editCategory != null || addingCategory) {
        CategoryEditor(editCategory, s.busy, s.error, vm) { editCategory = null; addingCategory = false }
        return
    }
    Scaffold(topBar = { TopAppBar(title = { Text("Store Desk · ${s.section}") }, actions = {
        TextButton(onClick = vm::refresh) { Text("Refresh") }
        TextButton(onClick = vm::logout) { Text("Sign out") }
    }) }) { padding ->
        Column(Modifier.fillMaxSize().padding(padding)) {
            androidx.compose.foundation.lazy.LazyRow(Modifier.fillMaxWidth().padding(horizontal = 8.dp), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                items(sections) { section ->
                    FilterChip(selected = s.section == section, onClick = { vm.section(section) }, label = { Text(section) })
                }
            }
            if (s.error.isNotBlank()) Text(s.error, Modifier.padding(16.dp), color = MaterialTheme.colorScheme.error)
            if (s.notice.isNotBlank()) Text(s.notice, Modifier.padding(16.dp), color = MaterialTheme.colorScheme.primary)
            when (s.section) {
                "Dashboard" -> DashboardScreen(s, vm)
                "Orders" -> OrdersScreen(s, vm)
                "Products" -> ProductsScreen(s, vm) { addingProduct = true }
                "Categories" -> SimpleList(s.categories.map { it.name to it.active }, { addingCategory = true }, "Add category") { index -> editCategory = s.categories[index] }
                "Brands" -> SimpleList(s.brands.map { it.name to it.active }, { addingBrand = true }, "Add brand") { index -> editBrand = s.brands[index] }
            }
        }
    }
}

@Composable
private fun LoginScreen(s: AdminState, vm: AdminViewModel) {
    var username by rememberSaveable { mutableStateOf("") }
    var password by rememberSaveable { mutableStateOf("") }
    Column(Modifier.fillMaxSize().padding(24.dp), verticalArrangement = Arrangement.Center) {
        Text("goodgrocer", style = MaterialTheme.typography.headlineLarge)
        Text("STORE DESK", style = MaterialTheme.typography.labelLarge)
        Spacer(Modifier.height(24.dp))
        Text("Sign in to manage your store", style = MaterialTheme.typography.titleLarge)
        Field("Username", username) { username = it }
        OutlinedTextField(password, { password = it }, label = { Text("Password") }, visualTransformation = PasswordVisualTransformation(), singleLine = true, modifier = Modifier.fillMaxWidth())
        if (s.error.isNotBlank()) Text(s.error, color = MaterialTheme.colorScheme.error)
        Button(onClick = { vm.login(username, password); password = "" }, enabled = !s.busy && username.isNotBlank() && password.isNotBlank()) { Text("Sign in") }
    }
}

@Composable
private fun DashboardScreen(s: AdminState, vm: AdminViewModel) {
    val dashboard = s.dashboard ?: return
    LazyColumn(Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item { Text("Awaiting action: ${dashboard.awaiting_action}", style = MaterialTheme.typography.headlineSmall) }
        item { TextButton(onClick = { vm.status("PLACED"); vm.section("Orders") }) { Text("Review placed orders") } }
        item { Text("Today's orders: ${dashboard.today_orders}", style = MaterialTheme.typography.titleLarge) }
        item { Text("Unavailable products: ${dashboard.unavailable_products}", style = MaterialTheme.typography.titleLarge) }
        item { Text("Recent orders", style = MaterialTheme.typography.titleLarge) }
        items(dashboard.recent_orders) { OrderRow(it) { vm.openOrder(it.id) } }
    }
}

@Composable
private fun OrdersScreen(s: AdminState, vm: AdminViewModel) {
    LazyColumn(Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        item { Text("Refreshes every 30 seconds", style = MaterialTheme.typography.bodySmall) }
        item { ChoiceRow(listOf("All") + orderStatuses, s.status.ifBlank { "All" }) { vm.status(if (it == "All") "" else it) } }
        items(s.orders) { OrderRow(it) { vm.openOrder(it.id) } }
        item { Pager(s.page, s.orders.size == 20, vm::page) }
    }
}

@Composable
private fun OrderRow(order: Order, open: () -> Unit) {
    Column(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
        Text("${order.order_number} · ${money(order.total)}", style = MaterialTheme.typography.titleMedium)
        Text("${order.status.replace('_', ' ')} · ${order.fulfilment_type} · ${order.customer_phone}")
        Text("${order.payment_method.replace('_', ' ')} · ${order.payment_status}")
        TextButton(onClick = open) { Text("Open order") }
        HorizontalDivider()
    }
}

@Composable
private fun OrderScreen(order: Order, busy: Boolean, error: String, vm: AdminViewModel) {
    var reason by remember(order.id) { mutableStateOf("") }
    val transitions = when (order.status) {
        "PLACED" -> listOf("ACCEPTED", "CANCELLED")
        "ACCEPTED" -> if (order.fulfilment_type == "PICKUP") listOf("DELIVERED", "CANCELLED") else listOf("OUT_FOR_DELIVERY", "CANCELLED")
        "OUT_FOR_DELIVERY" -> listOf("DELIVERED", "CANCELLED")
        else -> emptyList()
    }
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        TextButton(onClick = vm::closeOrder) { Text("← Orders") }
        if (error.isNotBlank()) Text(error, color = MaterialTheme.colorScheme.error)
        Text(order.order_number, style = MaterialTheme.typography.headlineMedium)
        Text("${order.status.replace('_', ' ')} · ${order.fulfilment_type}")
        Text("${order.customer_phone} · ${money(order.total)}")
        Text("${order.payment_method.replace('_', ' ')} · ${order.payment_status}")
        order.address_snapshot?.let { address -> Text("Delivery: " + listOf("recipient_name", "line1", "line2", "locality", "city", "postal_code").mapNotNull { address[it]?.toString() }.filter { it.isNotBlank() }.joinToString(", ")) }
        order.items.forEach { Text("${it.quantity} × ${it.product_name} · ${it.variant_name} — ${money(it.line_total)}") }
        if ("CANCELLED" in transitions) Field("Cancellation reason", reason) { reason = it }
        transitions.forEach { target ->
            OutlinedButton(onClick = { vm.transition(target, if (target == "CANCELLED") reason else null) {} }, enabled = !busy && (target != "CANCELLED" || reason.isNotBlank())) { Text(if (target == "CANCELLED") "Cancel order" else "Mark ${target.replace('_', ' ').lowercase()}") }
        }
        if (order.payment_status != "PAID" && order.payment_method != "ONLINE_UPI" && order.status != "CANCELLED") {
            Button(onClick = { vm.markPaid {} }, enabled = !busy) { Text("Mark payment received") }
        }
    }
}

@Composable
private fun ProductsScreen(s: AdminState, vm: AdminViewModel, add: () -> Unit) {
    LazyColumn(Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        item { Field("Search products", s.query, vm::query) }
        item { ChoiceRow(listOf("All categories") + s.categories.map { it.name }, s.categories.firstOrNull { it.id == s.category }?.name ?: "All categories") { label -> vm.category(s.categories.firstOrNull { it.name == label }?.id) } }
        item { ChoiceRow(listOf("All", "Available", "Unavailable"), when (s.availability) { true -> "Available"; false -> "Unavailable"; null -> "All" }) { vm.availability(when (it) { "Available" -> true; "Unavailable" -> false; else -> null }) } }
        item { Button(onClick = add) { Text("Add product") } }
        items(s.products?.items ?: emptyList()) { product ->
            Column(Modifier.fillMaxWidth()) {
                Text(product.name, style = MaterialTheme.typography.titleMedium)
                Text("${product.brand.name} · ${product.categories.joinToString { it.name }}")
                Text(if (!product.active) "Inactive" else if (product.available) "Available" else "Unavailable")
                TextButton(onClick = { vm.openProduct(product.id) }) { Text("Edit product") }
                HorizontalDivider()
            }
        }
        item { Text("${s.products?.total ?: 0} products") }
        item { Pager(s.page, (s.products?.let { it.page * it.page_size < it.total } == true), vm::page) }
    }
}

@Composable
private fun SimpleList(rows: List<Pair<String, Boolean>>, add: () -> Unit, label: String, edit: (Int) -> Unit) {
    LazyColumn(Modifier.fillMaxSize().padding(16.dp)) {
        item { Button(onClick = add) { Text(label) } }
        items(rows.size) { index ->
            Text(rows[index].first, style = MaterialTheme.typography.titleMedium)
            Text(if (rows[index].second) "Active" else "Inactive")
            TextButton(onClick = { edit(index) }) { Text("Edit") }
            HorizontalDivider()
        }
    }
}

@Composable
private fun Pager(page: Int, hasNext: Boolean, change: (Int) -> Unit) {
    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        OutlinedButton(onClick = { change(page - 1) }, enabled = page > 1) { Text("Previous") }
        Text("Page $page", Modifier.padding(top = 12.dp))
        OutlinedButton(onClick = { change(page + 1) }, enabled = hasNext) { Text("Next") }
    }
}

@Composable
private fun ChoiceRow(options: List<String>, selected: String, choose: (String) -> Unit) {
    androidx.compose.foundation.lazy.LazyRow(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
        items(options) { option -> FilterChip(selected = selected == option, onClick = { choose(option) }, label = { Text(option.replace('_', ' ')) }) }
    }
}

@Composable
private fun Field(label: String, value: String, change: (String) -> Unit) {
    OutlinedTextField(value, change, label = { Text(label) }, modifier = Modifier.fillMaxWidth())
}

@Composable
private fun Flag(label: String, value: Boolean, change: (Boolean) -> Unit) {
    Row { Checkbox(value, change); Text(label, Modifier.padding(top = 12.dp)) }
}
