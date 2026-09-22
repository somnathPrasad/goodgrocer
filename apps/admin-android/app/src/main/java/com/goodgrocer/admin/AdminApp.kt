package com.goodgrocer.admin

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.Logout
import androidx.compose.material.icons.automirrored.filled.ReceiptLong
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Category
import androidx.compose.material.icons.filled.ChevronRight
import androidx.compose.material.icons.filled.Dashboard
import androidx.compose.material.icons.filled.Inventory2
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Sell
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.FilterChip
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import java.math.BigDecimal
import java.text.NumberFormat
import java.util.Locale

private val sections = listOf("Dashboard", "Orders", "Products", "Categories", "Brands")
private val orderStatuses = listOf("PLACED", "ACCEPTED", "OUT_FOR_DELIVERY", "DELIVERED", "CANCELLED")
private fun money(value: String) = runCatching { NumberFormat.getCurrencyInstance(Locale.forLanguageTag("en-IN")).format(BigDecimal(value)) }.getOrDefault(value)
private fun label(value: String) = value.replace('_', ' ').lowercase().replaceFirstChar { it.uppercase() }

@Composable
fun AdminApp(vm: AdminViewModel) {
    val s by vm.state.collectAsState()
    if (s.signedIn == null) {
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { Text("Opening store desk…") }
        return
    }
    if (s.signedIn == false) { LoginScreen(s, vm); return }
    var editBrand by remember { mutableStateOf<Brand?>(null) }
    var editCategory by remember { mutableStateOf<Category?>(null) }
    var addingBrand by remember { mutableStateOf(false) }
    var addingCategory by remember { mutableStateOf(false) }
    var addingProduct by remember { mutableStateOf(false) }
    if (s.selectedOrder != null) { OrderScreen(s.selectedOrder!!, s.busy, s.error, vm); return }
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
    Scaffold(
        containerColor = Paper,
        topBar = {
            Surface(color = Forest) {
                Row(Modifier.fillMaxWidth().statusBarsPadding().padding(start = 20.dp, end = 8.dp, top = 12.dp, bottom = 12.dp), verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f)) {
                        Text("goodgrocer", style = MaterialTheme.typography.titleLarge, color = Color.White)
                        Text("STORE DESK", style = MaterialTheme.typography.labelLarge, color = Lime)
                    }
                    IconButton(onClick = vm::refresh, enabled = !s.busy) { Icon(Icons.Default.Refresh, "Refresh", tint = Color.White) }
                    IconButton(onClick = vm::logout) { Icon(Icons.AutoMirrored.Filled.Logout, "Sign out", tint = Color.White) }
                }
            }
        },
        bottomBar = {
            NavigationBar(containerColor = Color.White) {
                val icons = listOf(Icons.Default.Dashboard, Icons.AutoMirrored.Filled.ReceiptLong, Icons.Default.Inventory2, Icons.Default.Category, Icons.Default.Sell)
                sections.forEachIndexed { index, section ->
                    NavigationBarItem(
                        selected = s.section == section,
                        onClick = { if (s.section != section) vm.section(section) },
                        icon = { Icon(icons[index], contentDescription = null) },
                        label = { Text(section, maxLines = 1) },
                        alwaysShowLabel = true
                    )
                }
            }
        }
    ) { padding ->
        Column(Modifier.fillMaxSize().padding(padding)) {
            if (s.error.isNotBlank()) Message(s.error, true)
            if (s.notice.isNotBlank()) Message(s.notice, false)
            when (s.section) {
                "Dashboard" -> DashboardScreen(s, vm)
                "Orders" -> OrdersScreen(s, vm)
                "Products" -> ProductsScreen(s, vm) { addingProduct = true }
                "Categories" -> SimpleList("Categories", "Organise how shoppers browse", s.categories.map { it.name to it.active }, { addingCategory = true }, "Add category") { editCategory = s.categories[it] }
                "Brands" -> SimpleList("Brands", "Keep your catalogue organised", s.brands.map { it.name to it.active }, { addingBrand = true }, "Add brand") { editBrand = s.brands[it] }
            }
        }
    }
}

@Composable
fun Message(value: String, error: Boolean) {
    Surface(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp), shape = RoundedCornerShape(12.dp), color = if (error) Color(0xFFFCE7E3) else Color(0xFFDFF0E6)) {
        Text(value, Modifier.padding(14.dp), color = if (error) Danger else Forest)
    }
}

@Composable
private fun PageHeading(eyebrow: String, title: String, subtitle: String? = null) {
    Column(Modifier.fillMaxWidth().padding(bottom = 8.dp)) {
        Text(eyebrow.uppercase(), style = MaterialTheme.typography.labelLarge, color = Green)
        Text(title, style = MaterialTheme.typography.headlineLarge)
        if (subtitle != null) Text(subtitle, style = MaterialTheme.typography.bodyMedium, color = Muted)
    }
}

@Composable
private fun LoginScreen(s: AdminState, vm: AdminViewModel) {
    var username by rememberSaveable { mutableStateOf("") }
    var password by rememberSaveable { mutableStateOf("") }
    Box(Modifier.fillMaxSize().background(Forest).padding(20.dp), contentAlignment = Alignment.Center) {
        Card(shape = RoundedCornerShape(24.dp), colors = CardDefaults.cardColors(containerColor = Color.White)) {
            Column(Modifier.fillMaxWidth().padding(26.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
                Text("goodgrocer", style = MaterialTheme.typography.headlineMedium, color = Green)
                Text("STORE DESK", style = MaterialTheme.typography.labelLarge, color = Muted)
                Spacer(Modifier.height(10.dp))
                Text("Welcome back.", style = MaterialTheme.typography.headlineMedium)
                Text("Sign in to manage your neighbourhood store.", color = Muted)
                if (s.error.isNotBlank()) Message(s.error, true)
                Field("Username", username) { username = it }
                OutlinedTextField(password, { password = it }, label = { Text("Password") }, visualTransformation = PasswordVisualTransformation(), singleLine = true, modifier = Modifier.fillMaxWidth())
                Button(onClick = { vm.login(username, password); password = "" }, enabled = !s.busy && username.isNotBlank() && password.isNotBlank(), modifier = Modifier.fillMaxWidth().height(52.dp)) { Text(if (s.busy) "Signing in…" else "Sign in") }
            }
        }
    }
}

@Composable
private fun DashboardScreen(s: AdminState, vm: AdminViewModel) {
    val dashboard = s.dashboard
    LazyColumn(Modifier.fillMaxSize(), contentPadding = androidx.compose.foundation.layout.PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
        item { PageHeading("Your store at a glance", "Dashboard", "Today’s activity and what needs attention") }
        if (dashboard == null) { item { EmptyState("Loading your store…") }; return@LazyColumn }
        item {
            Surface(shape = CardShape, color = Lime, modifier = Modifier.fillMaxWidth().clickable { vm.status("PLACED"); vm.section("Orders") }) {
                Column(Modifier.padding(20.dp)) {
                    Text("AWAITING ACTION", style = MaterialTheme.typography.labelLarge, color = Forest)
                    Text("${dashboard.awaiting_action}", style = MaterialTheme.typography.headlineLarge, color = Forest)
                    Text("Review placed orders  →", style = MaterialTheme.typography.labelLarge, color = Forest)
                }
            }
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                StatCard("Today’s orders", dashboard.today_orders, Modifier.weight(1f)) { vm.section("Orders") }
                StatCard("Unavailable", dashboard.unavailable_products, Modifier.weight(1f)) { vm.availability(false); vm.section("Products") }
            }
        }
        item { Text("Recent orders", style = MaterialTheme.typography.titleLarge, modifier = Modifier.padding(top = 10.dp)) }
        if (dashboard.recent_orders.isEmpty()) item { EmptyState("No recent orders yet") }
        items(dashboard.recent_orders, key = { it.id }) { OrderRow(it) { vm.openOrder(it.id) } }
    }
}

@Composable
private fun StatCard(title: String, count: Int, modifier: Modifier, open: () -> Unit) {
    Surface(modifier.clickable(onClick = open), shape = CardShape, color = Color.White, border = androidx.compose.foundation.BorderStroke(1.dp, Line)) {
        Column(Modifier.padding(18.dp)) {
            Text(title, style = MaterialTheme.typography.bodyMedium, color = Muted)
            Text("$count", style = MaterialTheme.typography.headlineLarge)
            Text("View details  →", style = MaterialTheme.typography.labelLarge, color = Green)
        }
    }
}

@Composable
private fun OrdersScreen(s: AdminState, vm: AdminViewModel) {
    LazyColumn(Modifier.fillMaxSize(), contentPadding = androidx.compose.foundation.layout.PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item { PageHeading("Order management", "Orders", "Updates automatically every 30 seconds") }
        item { ChoiceRow(listOf("All") + orderStatuses, s.status.ifBlank { "All" }) { vm.status(if (it == "All") "" else it) } }
        if (s.orders.isEmpty()) item { EmptyState("No orders in this view") }
        items(s.orders, key = { it.id }) { OrderRow(it) { vm.openOrder(it.id) } }
        item { Pager(s.page, s.orders.size == 20, vm::page) }
    }
}

@Composable
private fun OrderRow(order: Order, open: () -> Unit) {
    Surface(Modifier.fillMaxWidth().clickable(onClick = open), shape = CardShape, color = Color.White, border = androidx.compose.foundation.BorderStroke(1.dp, Line)) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(order.order_number, style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                StatusBadge(order.status)
            }
            Text(money(order.total), style = MaterialTheme.typography.headlineMedium)
            Text("${label(order.fulfilment_type)}  ·  ${order.customer_phone}", color = Muted, style = MaterialTheme.typography.bodyMedium)
            HorizontalDivider(color = Line)
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("${label(order.payment_method)}  ·  ${label(order.payment_status)}", style = MaterialTheme.typography.bodyMedium, color = Muted, modifier = Modifier.weight(1f))
                Icon(Icons.Default.ChevronRight, contentDescription = "Open order", tint = Green)
            }
        }
    }
}

@Composable
fun StatusBadge(status: String) {
    val (bg, fg) = when (status) {
        "PLACED" -> Color(0xFFFFF0C9) to Color(0xFF70540B)
        "ACCEPTED", "DELIVERED", "ACTIVE", "AVAILABLE" -> Color(0xFFDCEFE4) to Color(0xFF18583B)
        "OUT_FOR_DELIVERY" -> Color(0xFFDCEAFA) to Color(0xFF254F78)
        "CANCELLED", "INACTIVE", "UNAVAILABLE" -> Color(0xFFF9E3DF) to Color(0xFF923D33)
        else -> Color(0xFFEAF0ED) to Ink
    }
    Surface(shape = RoundedCornerShape(7.dp), color = bg) {
        Text(label(status), Modifier.padding(horizontal = 9.dp, vertical = 5.dp), style = MaterialTheme.typography.labelLarge, color = fg, maxLines = 1)
    }
}

@Composable
fun DetailHeader(back: () -> Unit, parent: String, title: String) {
    Column(Modifier.fillMaxWidth().background(Forest).statusBarsPadding().padding(start = 10.dp, end = 16.dp, top = 8.dp, bottom = 18.dp)) {
        TextButton(onClick = back) { Icon(Icons.AutoMirrored.Filled.ArrowBack, null, tint = Lime); Spacer(Modifier.width(8.dp)); Text(parent, color = Lime) }
        Text(title, Modifier.padding(start = 14.dp), style = MaterialTheme.typography.headlineMedium, color = Color.White)
    }
}

@Composable
private fun OrderScreen(order: Order, busy: Boolean, error: String, vm: AdminViewModel) {
    var reason by remember(order.id) { mutableStateOf("") }
    val next = when (order.status) {
        "PLACED" -> "ACCEPTED"
        "ACCEPTED" -> if (order.fulfilment_type == "PICKUP") "DELIVERED" else "OUT_FOR_DELIVERY"
        "OUT_FOR_DELIVERY" -> "DELIVERED"
        else -> null
    }
    Column(Modifier.fillMaxSize().background(Paper)) {
        DetailHeader(vm::closeOrder, "Orders", order.order_number)
        Column(Modifier.verticalScroll(rememberScrollState()).padding(16.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
            if (error.isNotBlank()) Message(error, true)
            Surface(shape = CardShape, color = Color.White, modifier = Modifier.fillMaxWidth()) {
                Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) { StatusBadge(order.status); Spacer(Modifier.weight(1f)); Text(money(order.total), style = MaterialTheme.typography.titleLarge) }
                    Text("${label(order.fulfilment_type)}  ·  ${order.customer_phone}", color = Muted)
                    Text("${label(order.payment_method)}  ·  ${label(order.payment_status)}", color = Muted)
                }
            }
            order.address_snapshot?.let { address ->
                InfoCard("Delivery address") { Text(listOf("recipient_name", "line1", "line2", "locality", "city", "postal_code").mapNotNull { address[it]?.toString() }.filter { it.isNotBlank() }.joinToString(", ")) }
            }
            InfoCard("Items") {
                order.items.forEachIndexed { index, item ->
                    if (index > 0) HorizontalDivider(color = Line, modifier = Modifier.padding(vertical = 8.dp))
                    Row {
                        Column(Modifier.weight(1f)) { Text(item.product_name, fontWeight = FontWeight.SemiBold); Text("${item.quantity} × ${item.variant_name}", color = Muted) }
                        Text(money(item.line_total), fontWeight = FontWeight.SemiBold)
                    }
                }
            }
            if (order.cancellation_reason != null) InfoCard("Cancellation reason") { Text(order.cancellation_reason) }
            if (next != null || (order.payment_status != "PAID" && order.payment_method != "ONLINE_UPI" && order.status != "CANCELLED")) {
                InfoCard("Actions") {
                    if (next != null) Button(onClick = { vm.transition(next, null) {} }, enabled = !busy, modifier = Modifier.fillMaxWidth().height(50.dp)) {
                        Text(when (next) { "ACCEPTED" -> "Accept order"; "DELIVERED" -> "Mark delivered / collected"; else -> "Out for delivery" })
                    }
                    if (order.payment_status != "PAID" && order.payment_method != "ONLINE_UPI" && order.status != "CANCELLED") {
                        OutlinedButton(onClick = { vm.markPaid {} }, enabled = !busy, modifier = Modifier.fillMaxWidth()) { Text("Mark payment received") }
                    }
                }
            }
            if (next != null) InfoCard("Cancel order") {
                Text("A reason is required to cancel this order.", color = Muted)
                Field("Cancellation reason", reason) { reason = it }
                OutlinedButton(onClick = { vm.transition("CANCELLED", reason.trim()) {} }, enabled = !busy && reason.isNotBlank(), modifier = Modifier.fillMaxWidth()) { Text("Cancel order", color = Danger) }
            }
            Spacer(Modifier.height(16.dp))
        }
    }
}

@Composable
fun InfoCard(title: String, content: @Composable androidx.compose.foundation.layout.ColumnScope.() -> Unit) {
    Surface(Modifier.fillMaxWidth(), shape = CardShape, color = Color.White, border = androidx.compose.foundation.BorderStroke(1.dp, Line)) {
        Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text(title, style = MaterialTheme.typography.titleMedium)
            content()
        }
    }
}

@Composable
private fun ProductsScreen(s: AdminState, vm: AdminViewModel, add: () -> Unit) {
    LazyColumn(Modifier.fillMaxSize(), contentPadding = androidx.compose.foundation.layout.PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item { PageHeading("Catalogue", "Products", "${s.products?.total ?: 0} products") }
        item { Button(onClick = add, modifier = Modifier.fillMaxWidth().height(50.dp)) { Icon(Icons.Default.Add, null); Spacer(Modifier.width(8.dp)); Text("Add product") } }
        item { Field("Search products", s.query, vm::query) }
        item { ChoiceRow(listOf("All", "Available", "Unavailable"), when (s.availability) { true -> "Available"; false -> "Unavailable"; null -> "All" }) { vm.availability(when (it) { "Available" -> true; "Unavailable" -> false; else -> null }) } }
        item { Text("Category", style = MaterialTheme.typography.labelLarge) }
        item { ChoiceRow(listOf("All categories") + s.categories.map { it.name }, s.categories.firstOrNull { it.id == s.category }?.name ?: "All categories") { selected -> vm.category(s.categories.firstOrNull { it.name == selected }?.id) } }
        if (s.products?.items?.isEmpty() == true) item { EmptyState("No products match these filters") }
        items(s.products?.items ?: emptyList(), key = { it.id }) { product ->
            Surface(Modifier.fillMaxWidth().clickable { vm.openProduct(product.id) }, shape = CardShape, color = Color.White, border = androidx.compose.foundation.BorderStroke(1.dp, Line)) {
                Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                    Box(Modifier.size(54.dp).background(Paper, RoundedCornerShape(12.dp)), contentAlignment = Alignment.Center) { Icon(Icons.Default.Inventory2, null, tint = Green) }
                    Spacer(Modifier.width(14.dp))
                    Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Text(product.name, style = MaterialTheme.typography.titleMedium, maxLines = 2, overflow = TextOverflow.Ellipsis)
                        Text(product.brand.name, color = Muted, style = MaterialTheme.typography.bodyMedium)
                        StatusBadge(if (!product.active) "INACTIVE" else if (product.available) "AVAILABLE" else "UNAVAILABLE")
                    }
                    Icon(Icons.Default.ChevronRight, "Edit product", tint = Green)
                }
            }
        }
        item { Pager(s.page, (s.products?.let { it.page * it.page_size < it.total } == true), vm::page) }
    }
}

@Composable
private fun SimpleList(title: String, subtitle: String, rows: List<Pair<String, Boolean>>, add: () -> Unit, addLabel: String, edit: (Int) -> Unit) {
    LazyColumn(Modifier.fillMaxSize(), contentPadding = androidx.compose.foundation.layout.PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item { PageHeading("Catalogue", title, subtitle) }
        item { Button(onClick = add, modifier = Modifier.fillMaxWidth().height(50.dp)) { Icon(Icons.Default.Add, null); Spacer(Modifier.width(8.dp)); Text(addLabel) } }
        if (rows.isEmpty()) item { EmptyState("No ${title.lowercase()} yet") }
        items(rows.size) { index ->
            Surface(Modifier.fillMaxWidth().clickable { edit(index) }, shape = CardShape, color = Color.White, border = androidx.compose.foundation.BorderStroke(1.dp, Line)) {
                Row(Modifier.padding(18.dp), verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(7.dp)) { Text(rows[index].first, style = MaterialTheme.typography.titleMedium); StatusBadge(if (rows[index].second) "ACTIVE" else "INACTIVE") }
                    Icon(Icons.Default.ChevronRight, "Edit ${rows[index].first}", tint = Green)
                }
            }
        }
    }
}

@Composable
private fun EmptyState(text: String) {
    Surface(Modifier.fillMaxWidth(), shape = CardShape, color = Color.White) { Text(text, Modifier.padding(26.dp), color = Muted) }
}

@Composable
private fun Pager(page: Int, hasNext: Boolean, change: (Int) -> Unit) {
    Row(Modifier.fillMaxWidth().padding(vertical = 6.dp), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
        OutlinedButton(onClick = { change(page - 1) }, enabled = page > 1) { Text("Previous") }
        Text("Page $page", color = Muted)
        OutlinedButton(onClick = { change(page + 1) }, enabled = hasNext) { Text("Next") }
    }
}

@Composable
fun ChoiceRow(options: List<String>, selected: String, choose: (String) -> Unit) {
    LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        items(options) { option -> FilterChip(selected = selected == option, onClick = { choose(option) }, label = { Text(label(option)) }) }
    }
}

@Composable
fun Field(label: String, value: String, change: (String) -> Unit) {
    OutlinedTextField(value, change, label = { Text(label) }, singleLine = true, modifier = Modifier.fillMaxWidth())
}
