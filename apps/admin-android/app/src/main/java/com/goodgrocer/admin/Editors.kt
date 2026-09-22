package com.goodgrocer.admin

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.FilterChip
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
import java.util.Locale

private fun makeSlug(value: String) = value.lowercase(Locale.ROOT).replace(Regex("[^a-z0-9]+"), "-").trim('-')

@Composable
fun BrandEditor(brand: Brand?, busy: Boolean, error: String, vm: AdminViewModel, close: () -> Unit) {
    var name by remember(brand?.id) { mutableStateOf(brand?.name ?: "") }
    var slug by remember(brand?.id) { mutableStateOf(brand?.slug ?: "") }
    var active by remember(brand?.id) { mutableStateOf(brand?.active ?: true) }
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        TextButton(onClick = close) { Text("← Brands") }
        if (error.isNotBlank()) Text(error, color = MaterialTheme.colorScheme.error)
        Text(if (brand == null) "Add brand" else "Edit brand", style = MaterialTheme.typography.headlineMedium)
        OutlinedTextField(name, { name = it; if (brand == null) slug = makeSlug(it) }, label = { Text("Name") }, modifier = Modifier.fillMaxWidth())
        OutlinedTextField(slug, { slug = it }, label = { Text("Slug") }, modifier = Modifier.fillMaxWidth())
        EditorFlag("Active", active) { active = it }
        Button(onClick = { vm.saveBrand(brand?.id, BrandInput(name, slug, active), close) }, enabled = !busy && name.isNotBlank() && slug.isNotBlank()) { Text("Save brand") }
    }
}

@Composable
fun CategoryEditor(category: Category?, busy: Boolean, error: String, vm: AdminViewModel, close: () -> Unit) {
    var name by remember(category?.id) { mutableStateOf(category?.name ?: "") }
    var slug by remember(category?.id) { mutableStateOf(category?.slug ?: "") }
    var active by remember(category?.id) { mutableStateOf(category?.active ?: true) }
    var order by remember(category?.id) { mutableStateOf(category?.display_order?.toString() ?: "0") }
    var image by remember(category?.id) { mutableStateOf(category?.image_url) }
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        TextButton(onClick = close) { Text("← Categories") }
        if (error.isNotBlank()) Text(error, color = MaterialTheme.colorScheme.error)
        Text(if (category == null) "Add category" else "Edit category", style = MaterialTheme.typography.headlineMedium)
        OutlinedTextField(name, { name = it; if (category == null) slug = makeSlug(it) }, label = { Text("Name") }, modifier = Modifier.fillMaxWidth())
        EditorField("Slug", slug) { slug = it }
        EditorField("Display order", order) { order = it }
        ImagePicker(image, vm) { image = it }
        EditorFlag("Active", active) { active = it }
        Button(onClick = { vm.saveCategory(category?.id, CategoryInput(name, slug, active, image, order.toIntOrNull() ?: 0), close) }, enabled = !busy && name.isNotBlank() && slug.isNotBlank() && order.toIntOrNull() != null) { Text("Save category") }
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
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        TextButton(onClick = close) { Text("← Products") }
        if (s.error.isNotBlank()) Text(s.error, color = MaterialTheme.colorScheme.error)
        Text(if (product == null) "Add product" else "Edit product", style = MaterialTheme.typography.headlineMedium)
        OutlinedTextField(name, { name = it; if (product == null) slug = makeSlug(it) }, label = { Text("Name") }, modifier = Modifier.fillMaxWidth())
        EditorField("Slug", slug) { slug = it }
        EditorField("Description", description) { description = it }
        ImagePicker(image, vm) { image = it }
        Text("Brand")
        s.brands.forEach { brand -> FilterChip(selected = brandId == brand.id, onClick = { brandId = brand.id }, label = { Text(brand.name) }) }
        Text("Categories · choose any number")
        s.categories.forEach { category ->
            FilterChip(selected = category.id in categoryIds, onClick = {
                categoryIds = if (category.id in categoryIds) categoryIds - category.id else categoryIds + category.id
            }, label = { Text(category.name) })
        }
        EditorFlag("Active", active) { active = it }
        EditorFlag("Available", available) { available = it }
        Button(onClick = {
            vm.saveProduct(product?.id, ProductInput(name, slug, description, image, active, available, brandId ?: return@Button, categoryIds)) {
                if (product == null) close()
            }
        }, enabled = !s.busy && name.isNotBlank() && slug.isNotBlank() && brandId != null) { Text("Save product") }
        if (product != null) {
            Text("Variants", style = MaterialTheme.typography.titleLarge)
            product.variants.forEach { item ->
                Text("${item.name} · ₹${item.selling_price} / ₹${item.mrp} · ${if (item.available) "Available" else "Unavailable"}")
                TextButton(onClick = { variant = item }) { Text("Edit variant") }
            }
            OutlinedButton(onClick = { addingVariant = true }) { Text("Add variant") }
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
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        TextButton(onClick = close) { Text("← Product") }
        if (error.isNotBlank()) Text(error, color = MaterialTheme.colorScheme.error)
        Text(if (variant == null) "Add variant" else "Edit variant", style = MaterialTheme.typography.headlineMedium)
        EditorField("Variant label", name) { name = it }
        EditorField("MRP (₹)", mrp) { mrp = it }
        EditorField("Selling price (₹)", price) { price = it }
        EditorField("Display order", order) { order = it }
        EditorFlag("Active", active) { active = it }
        EditorFlag("Available", available) { available = it }
        Button(onClick = { vm.saveVariant(product.id, variant?.id, VariantInput(name, mrp, price, active, available, order.toIntOrNull() ?: 0), close) }, enabled = !busy && name.isNotBlank() && mrp.toBigDecimalOrNull() != null && price.toBigDecimalOrNull() != null && order.toIntOrNull() != null) { Text("Save variant") }
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
    Text(image ?: "No image selected")
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
    FilterChip(selected = value, onClick = { change(!value) }, label = { Text("$label: ${if (value) "Yes" else "No"}") })
}
