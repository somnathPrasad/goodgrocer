package com.goodgrocer.admin

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Switch
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import coil.compose.AsyncImage
import java.util.Locale

private fun makeSlug(value: String) = value.lowercase(Locale.ROOT).replace(Regex("[^a-z0-9]+"), "-").trim('-')

@Composable
private fun EditorPage(parent: String, title: String, close: () -> Unit, content: @Composable ColumnScope.() -> Unit) {
    Column(Modifier.fillMaxSize().background(Paper)) {
        DetailHeader(close, parent, title)
        Column(
            Modifier.fillMaxSize().verticalScroll(rememberScrollState()).navigationBarsPadding().padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
            content = content
        )
    }
}

@Composable
fun BrandEditor(brand: Brand?, busy: Boolean, error: String, vm: AdminViewModel, close: () -> Unit) {
    var name by remember(brand?.id) { mutableStateOf(brand?.name ?: "") }
    var slug by remember(brand?.id) { mutableStateOf(brand?.slug ?: "") }
    var active by remember(brand?.id) { mutableStateOf(brand?.active ?: true) }
    EditorPage("Brands", if (brand == null) "Add brand" else "Edit brand", close) {
        if (error.isNotBlank()) Text(error, color = MaterialTheme.colorScheme.error)
        InfoCard("Brand details") {
            OutlinedTextField(name, { name = it; if (brand == null) slug = makeSlug(it) }, label = { Text("Name") }, modifier = Modifier.fillMaxWidth())
            OutlinedTextField(slug, { slug = it }, label = { Text("Slug") }, modifier = Modifier.fillMaxWidth())
        }
        InfoCard("Visibility") { EditorFlag("Active", active) { active = it } }
        Button(onClick = { vm.saveBrand(brand?.id, BrandInput(name, slug, active), close) }, enabled = !busy && name.isNotBlank() && slug.isNotBlank(), modifier = Modifier.fillMaxWidth().height(52.dp)) { Text("Save brand") }
    }
}

@Composable
fun CategoryEditor(category: Category?, busy: Boolean, error: String, vm: AdminViewModel, close: () -> Unit) {
    var name by remember(category?.id) { mutableStateOf(category?.name ?: "") }
    var slug by remember(category?.id) { mutableStateOf(category?.slug ?: "") }
    var active by remember(category?.id) { mutableStateOf(category?.active ?: true) }
    var order by remember(category?.id) { mutableStateOf(category?.display_order?.toString() ?: "0") }
    var image by remember(category?.id) { mutableStateOf(category?.image_url) }
    EditorPage("Categories", if (category == null) "Add category" else "Edit category", close) {
        if (error.isNotBlank()) Text(error, color = MaterialTheme.colorScheme.error)
        InfoCard("Category details") {
            OutlinedTextField(name, { name = it; if (category == null) slug = makeSlug(it) }, label = { Text("Name") }, modifier = Modifier.fillMaxWidth())
            EditorField("Slug", slug) { slug = it }
            EditorField("Display order", order) { order = it }
        }
        InfoCard("Category image") { ImagePicker(image, vm) { image = it } }
        InfoCard("Visibility") { EditorFlag("Active", active) { active = it } }
        Button(onClick = { vm.saveCategory(category?.id, CategoryInput(name, slug, active, image, order.toIntOrNull() ?: 0), close) }, enabled = !busy && name.isNotBlank() && slug.isNotBlank() && order.toIntOrNull() != null, modifier = Modifier.fillMaxWidth().height(52.dp)) { Text("Save category") }
    }
}

@Composable
fun ProductEditor(product: Product?, s: AdminState, vm: AdminViewModel, close: () -> Unit) {
    var name by remember(product?.id) { mutableStateOf(product?.name ?: "") }
    var slug by remember(product?.id) { mutableStateOf(product?.slug ?: "") }
    var description by remember(product?.id) { mutableStateOf(product?.description ?: "") }
    var image by remember(product?.id) { mutableStateOf(product?.image_url) }
    var brandId by remember(product?.id) { mutableStateOf(product?.brand_id ?: s.brands.firstOrNull()?.id) }
    var categoryIds: List<Int> by remember(product?.id) { mutableStateOf(product?.categories?.map { it.id } ?: emptyList()) }
    var active by remember(product?.id) { mutableStateOf(product?.active ?: true) }
    var available by remember(product?.id) { mutableStateOf(product?.available ?: true) }
    var variant by remember { mutableStateOf<Variant?>(null) }
    var addingVariant by remember { mutableStateOf(false) }
    if (variant != null || addingVariant) {
        VariantEditor(product ?: return, variant, s.busy, s.error, vm) { variant = null; addingVariant = false }
        return
    }
    EditorPage("Products", if (product == null) "Add product" else "Edit product", close) {
        if (s.error.isNotBlank()) Text(s.error, color = MaterialTheme.colorScheme.error)
        InfoCard("Product details") {
            OutlinedTextField(name, { name = it; if (product == null) slug = makeSlug(it) }, label = { Text("Name") }, modifier = Modifier.fillMaxWidth())
            EditorField("Slug", slug) { slug = it }
            OutlinedTextField(description, { description = it }, label = { Text("Description") }, minLines = 3, modifier = Modifier.fillMaxWidth())
        }
        InfoCard("Product image") { ImagePicker(image, vm) { image = it } }
        InfoCard("Organisation") {
            Text("Brand", style = MaterialTheme.typography.labelLarge)
            ChoiceRow(s.brands.map { it.name }, s.brands.firstOrNull { it.id == brandId }?.name ?: "") { choice -> brandId = s.brands.firstOrNull { it.name == choice }?.id }
            Text("Categories · choose any number", style = MaterialTheme.typography.labelLarge)
            androidx.compose.foundation.layout.FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                s.categories.forEach { category ->
                    FilterChip(selected = category.id in categoryIds, onClick = {
                        categoryIds = if (category.id in categoryIds) categoryIds - category.id else categoryIds + category.id
                    }, label = { Text(category.name) })
                }
            }
        }
        InfoCard("Availability") {
            EditorFlag("Active", active) { active = it }
            EditorFlag("Available", available) { available = it }
        }
        Button(onClick = {
            vm.saveProduct(product?.id, ProductInput(name, slug, description, image, active, available, brandId ?: return@Button, categoryIds)) {
                if (product == null) close()
            }
        }, enabled = !s.busy && name.isNotBlank() && slug.isNotBlank() && brandId != null, modifier = Modifier.fillMaxWidth().height(52.dp)) { Text("Save product") }
        if (product != null) {
            InfoCard("Variants") {
                product.variants.forEach { item ->
                    Text(item.name, style = MaterialTheme.typography.titleMedium)
                    Text("₹${item.selling_price} · MRP ₹${item.mrp}", color = Muted)
                    StatusBadge(if (!item.active) "INACTIVE" else if (item.available) "AVAILABLE" else "UNAVAILABLE")
                    TextButton(onClick = { variant = item }) { Text("Edit variant") }
                }
                OutlinedButton(onClick = { addingVariant = true }, modifier = Modifier.fillMaxWidth()) { Text("Add variant") }
            }
        }
    }
}

@Composable
fun VariantEditor(product: Product, variant: Variant?, busy: Boolean, error: String, vm: AdminViewModel, close: () -> Unit) {
    var name by remember(variant?.id) { mutableStateOf(variant?.name ?: "") }
    var mrp by remember(variant?.id) { mutableStateOf(variant?.mrp ?: "0.00") }
    var price by remember(variant?.id) { mutableStateOf(variant?.selling_price ?: "0.00") }
    var order by remember(variant?.id) { mutableStateOf(variant?.display_order?.toString() ?: "0") }
    var active by remember(variant?.id) { mutableStateOf(variant?.active ?: true) }
    var available by remember(variant?.id) { mutableStateOf(variant?.available ?: true) }
    EditorPage(product.name, if (variant == null) "Add variant" else "Edit variant", close) {
        if (error.isNotBlank()) Text(error, color = MaterialTheme.colorScheme.error)
        InfoCard("Variant details") {
            EditorField("Variant label", name) { name = it }
            EditorField("MRP (₹)", mrp) { mrp = it }
            EditorField("Selling price (₹)", price) { price = it }
            EditorField("Display order", order) { order = it }
        }
        InfoCard("Availability") {
            EditorFlag("Active", active) { active = it }
            EditorFlag("Available", available) { available = it }
        }
        Button(onClick = { vm.saveVariant(product.id, variant?.id, VariantInput(name, mrp, price, active, available, order.toIntOrNull() ?: 0), close) }, enabled = !busy && name.isNotBlank() && mrp.toBigDecimalOrNull() != null && price.toBigDecimalOrNull() != null && order.toIntOrNull() != null, modifier = Modifier.fillMaxWidth().height(52.dp)) { Text("Save variant") }
    }
}

@Composable
private fun ImagePicker(image: String?, vm: AdminViewModel, change: (String?) -> Unit) {
    val context = LocalContext.current
    val picker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri: Uri? ->
        if (uri != null) {
            val mime = context.contentResolver.getType(uri) ?: ""
            if (mime in listOf("image/jpeg", "image/png", "image/webp")) {
                context.contentResolver.openInputStream(uri)?.use { input ->
                    val bytes = input.readBytes()
                    vm.upload(bytes, mime) { change(it) }
                }
            }
        }
    }
    if (image != null) {
        val url = if (image.startsWith("http")) image else BuildConfig.API_URL.trimEnd('/') + "/" + image.trimStart('/')
        AsyncImage(model = url, contentDescription = "Selected image", modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp).height(150.dp), contentScale = androidx.compose.ui.layout.ContentScale.Fit)
    } else Text("No image selected", color = Muted)
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        OutlinedButton(onClick = { picker.launch("image/*") }) { Text("Upload image") }
        if (image != null) TextButton(onClick = { change(null) }) { Text("Remove") }
    }
}

@Composable
private fun EditorField(label: String, value: String, change: (String) -> Unit) {
    OutlinedTextField(value, change, label = { Text(label) }, modifier = Modifier.fillMaxWidth())
}

@Composable
private fun EditorFlag(label: String, value: Boolean, change: (Boolean) -> Unit) {
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
        Text(label, Modifier.padding(top = 12.dp), style = MaterialTheme.typography.titleMedium)
        Switch(checked = value, onCheckedChange = change)
    }
}
