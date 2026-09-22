package com.goodgrocer.app.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.GridItemSpan
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.grid.rememberLazyGridState
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Favorite
import androidx.compose.material.icons.outlined.FavoriteBorder
import androidx.compose.material.icons.outlined.Search
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedCard
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.platform.LocalSoftwareKeyboardController
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.goodgrocer.app.data.CartLine
import com.goodgrocer.app.data.cartSubtotal
import java.math.BigDecimal

@Composable
fun CatalogueScreen(
    vm: ShopViewModel,
    cart: List<CartLine>,
    home: Boolean = false,
    categoryId: Int? = null,
    open: (Int) -> Unit,
    autoFocusSearch: Boolean = false,
    search: () -> Unit = {
    },
    category: (Int) -> Unit = {}
) {
    val state = collectShopState(vm)
    var query by rememberSaveable { mutableStateOf("") }
    val visibleQuery = if (home || categoryId != null) "" else query
    val catalogueMatches = state.query == visibleQuery && state.category == categoryId
    val products = if (catalogueMatches) state.products else emptyList()
    val gridState = rememberLazyGridState()
    val focusRequester = remember { FocusRequester() }
    val keyboardController = LocalSoftwareKeyboardController.current
    LaunchedEffect(autoFocusSearch) {
        if (autoFocusSearch) {
            androidx.compose.runtime.withFrameNanos { }
            focusRequester.requestFocus()
            keyboardController?.show()
        }
    }
    LaunchedEffect(home, categoryId, autoFocusSearch) {
        vm.browse(query = visibleQuery, category = categoryId)
    }
    LazyVerticalGrid(
        columns = GridCells.Adaptive(155.dp),
        state = gridState,
        contentPadding = PaddingValues(16.dp),
        horizontalArrangement = Arrangement.spacedBy(12.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item(span = { GridItemSpan(maxLineSpan) }) {
            Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
                if (home) {
                    Row(
                        Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            "goodgrocer",
                            style = MaterialTheme.typography.titleLarge,
                            color = Forest
                        )
                        Text(
                            "YOUR LOCAL STORE",
                            style = MaterialTheme.typography.labelSmall,
                            color = Forest
                        )
                    }
                    Surface(
                        color = MaterialTheme.colorScheme.primaryContainer,
                        shape = MaterialTheme.shapes.large
                    ) {
                        Column(Modifier.fillMaxWidth().padding(24.dp)) {
                            Text(
                                "Grocery\nClose to home.",
                                style = MaterialTheme.typography.headlineLarge
                            )
                            Spacer(Modifier.height(10.dp))
                            Text(
                                "Everyday essentials from your neighbourhood store.",
                                style = MaterialTheme.typography.bodyMedium
                            )
                        }
                    }
                    OutlinedCard(onClick = search, modifier = Modifier.fillMaxWidth()) {
                        Row(
                            Modifier.padding(16.dp),
                            horizontalArrangement = Arrangement.spacedBy(12.dp)
                        ) {
                            Icon(Icons.Outlined.Search, null)
                            Text("Search your everyday essentials")
                        }
                    }
                    SectionTitle("Shop by aisle")
                    LazyRow(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        items(state.categories, key = {
                            it.id
                        }) { c ->
                            Column(
                                Modifier.width(92.dp).clickable {
                                    category(c.id)
                                },
                                horizontalAlignment = Alignment.CenterHorizontally,
                                verticalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                ProductImage(c.image_url, Modifier.size(76.dp))
                                Text(
                                    c.name,
                                    style = MaterialTheme.typography.labelMedium,
                                    minLines = 2
                                )
                            }
                        }
                    }
                    SectionTitle("Your daily essentials", "Selected by your local store")
                } else if (categoryId !=
                    null
                ) {
                    SectionTitle(
                        state.categories.firstOrNull {
                            it.id == categoryId
                        }?.name ?: "Category",
                        "Find your favourites in this aisle"
                    )
                } else {
                    OutlinedTextField(
                        value = query,
                        onValueChange = {
                            query = it
                            vm.browse(query = it)
                        },
                        modifier = Modifier.fillMaxWidth().focusRequester(
                            focusRequester
                        ),
                        placeholder = {
                            Text("Search products")
                        },
                        leadingIcon = {
                            Icon(Icons.Outlined.Search, null)
                        },
                        trailingIcon = if (query.isNotEmpty()) {
                            {
                                TextButton(onClick = {
                                    query = ""
                                    vm.browse()
                                }) { Text("Clear") }
                            }
                        } else {
                            null
                        },
                        singleLine = true,
                        shape = MaterialTheme.shapes.medium
                    )
                    if (query.isBlank()) {
                        SectionTitle("Browse all products", "Search above to find an item by name.")
                    } else {
                        SectionTitle("Results for “$query”")
                    }
                }
            }
        }
        if (catalogueMatches && state.catalogueLoading && products.isNotEmpty()) {
            item(span = { GridItemSpan(maxLineSpan) }) {
                LinearProgressIndicator(Modifier.fillMaxWidth())
            }
        }
        if (!catalogueMatches || state.catalogueLoading && products.isEmpty()
        ) {
            item(span = { GridItemSpan(maxLineSpan) }) { LoadingState() }
        }
        if (catalogueMatches && !state.catalogueLoading && state.catalogueError != null) {
            item(span = { GridItemSpan(maxLineSpan) }) {
                EmptyState(
                    "Couldn’t load products",
                    state.catalogueError,
                    "Retry",
                    { vm.browse(visibleQuery, categoryId, force = true) }
                )
            }
        } else if (catalogueMatches && !state.catalogueLoading && products.isEmpty()
        ) {
            item(span = {
                GridItemSpan(maxLineSpan)
            }) {
                when {
                    categoryId != null -> EmptyState(
                        "No products in this aisle yet",
                        "Explore another aisle or check back later.",
                        "Refresh",
                        { vm.browse(category = categoryId, force = true) }
                    )
                    query.isNotBlank() -> EmptyState(
                        "No matches for “$query”",
                        "Try another product name.",
                        "Clear search",
                        {
                            query = ""
                            vm.browse()
                        }
                    )
                    else -> EmptyState(
                        "No products available yet",
                        "Check back later for products from your store.",
                        "Refresh",
                        { vm.browse(force = true) }
                    )
                }
            }
        }
        items(products, key = { it.id }) { p ->
            val first =
                p.variants.firstOrNull { it.available } ?: p.variants.firstOrNull()
            ProductCard(
                p,
                cart.firstOrNull {
                    it.variant.id == first?.id
                }?.quantity ?: 0,
                { open(p.id) },
                { v, q -> vm.quantity(p, v, q) }
            )
        }
        if (catalogueMatches && products.size < state.total
        ) {
            item(span = {
                GridItemSpan(maxLineSpan)
            }) {
                OutlinedButton(onClick = {
                    vm.browse(query, categoryId, true)
                }, enabled = !state.catalogueLoading, modifier = Modifier.fillMaxWidth()) {
                    Text(if (state.catalogueLoading) "Loading…" else "Load more")
                }
            }
        }
    }
}

@Composable
fun ProductScreen(
    id: Int,
    vm: ShopViewModel,
    cart: List<CartLine>,
    signedIn: Boolean,
    login: () -> Unit
) {
    val state = collectShopState(vm)
    LaunchedEffect(id) {
        vm.loadProduct(id)
        if (signedIn) vm.loadFavourites()
    }
    val product = state.product?.takeIf { it.id == id }
    var selected by rememberSaveable(id) { mutableStateOf<Int?>(null) }
    if (product ==
        null
    ) {
        if (state.productLoading) {
            LoadingState()
        } else {
            EmptyState("Couldn’t open this product", "Please try again.", "Retry", {
                vm.loadProduct(id)
            })
        }
        return
    }
    val variant =
        product.variants.firstOrNull { it.id == selected }
            ?: product.variants.firstOrNull { it.available }
            ?: product.variants.firstOrNull()
    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        if (state.productLoading) LinearProgressIndicator(Modifier.fillMaxWidth())
        ProductImage(product.image_url, Modifier.fillMaxWidth().height(240.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text(
                    product.brand.name.uppercase(),
                    style = MaterialTheme.typography.labelMedium,
                    color = Forest
                )
                Text(product.name, style = MaterialTheme.typography.headlineLarge)
            }
            IconButton(onClick = { if (signedIn) vm.favourite(product) else login() }) {
                Icon(
                    if (state.favourites.any {
                            it.id ==
                                id
                        }
                    ) {
                        Icons.Outlined.Favorite
                    } else {
                        Icons.Outlined.FavoriteBorder
                    },
                    "Toggle favourite",
                    tint = Forest
                )
            }
        }
        Text(product.description, color = MaterialTheme.colorScheme.onSurfaceVariant)
        SectionTitle("Choose your size")
        product.variants.forEach { v ->
            OutlinedCard(
                onClick = {
                    selected = v.id
                },
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.outlinedCardColors(
                    containerColor = if (variant?.id ==
                        v.id
                    ) {
                        MaterialTheme.colorScheme.primaryContainer
                    } else {
                        MaterialTheme.colorScheme.surface
                    }
                )
            ) {
                Row(
                    Modifier.fillMaxWidth().padding(16.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    RadioButton(
                        selected =
                        variant?.id == v.id,
                        onClick = { selected = v.id }
                    )
                    Column(Modifier.weight(1f)) {
                        Text(v.name, fontWeight = FontWeight.Bold)
                        if (!v.available) {
                            Text(
                                "Unavailable",
                                color = MaterialTheme.colorScheme.error
                            )
                        }
                    }
                    Price(v)
                }
            }
        }
        if (variant !=
            null
        ) {
            Price(variant)
            val savingsText = remember(variant) {
                val mrp = variant.mrp.toBigDecimalOrNull() ?: BigDecimal.ZERO
                val selling = variant.selling_price.toBigDecimalOrNull() ?: BigDecimal.ZERO
                if (selling < mrp) {
                    "Save ${rupees((mrp - selling).toPlainString())}"
                } else {
                    null
                }
            }
            savingsText?.let {
                Text(it, color = Forest)
            }
            if (product.available &&
                variant.available
            ) {
                Quantity(
                    cart.firstOrNull {
                        it.variant.id == variant.id
                    }?.quantity ?: 0,
                    { vm.quantity(product, variant, it) }
                )
            } else {
                Text("Currently unavailable", color = MaterialTheme.colorScheme.error)
            }
        }
    }
}

@Composable
fun CartScreen(vm: ShopViewModel, cart: List<CartLine>, checkout: () -> Unit, shop: () -> Unit) {
    if (cart.isEmpty()) {
        EmptyState(
            "A little room for good things",
            "Your basket is empty. Find your daily essentials in the shop.",
            "Browse the shop",
            shop
        )
        return
    }
    LazyColumn(
        contentPadding = PaddingValues(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        item { SectionTitle("Your basket", "Prices and availability are checked at checkout") }
        items(cart, key = {
            it.variant.id
        }) { line ->
            Card(
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
            ) {
                Row(
                    Modifier.padding(14.dp),
                    verticalAlignment = Alignment.Top,
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    ProductImage(line.product.image_url, Modifier.size(68.dp))
                    Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Text(line.product.name, fontWeight = FontWeight.Bold)
                        Text(line.variant.name, style = MaterialTheme.typography.bodySmall)
                        Price(line.variant)
                        Quantity(line.quantity, { vm.quantity(line.product, line.variant, it) })
                        TextButton(onClick = {
                            vm.quantity(line.product, line.variant, 0)
                        }) { Text("Remove") }
                    }
                }
            }
        }
        item {
            val subtotalText = remember(cart) {
                rupees(cartSubtotal(cart).toPlainString())
            }
            HorizontalDivider()
            Row(
                Modifier.fillMaxWidth().padding(vertical = 20.dp),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text("Estimated subtotal")
                Text(subtotalText, fontWeight = FontWeight.Bold)
            }
            PrimaryButton("Continue to checkout", click = checkout)
        }
    }
}

@Composable
fun FavouritesScreen(vm: ShopViewModel, cart: List<CartLine>, open: (Int) -> Unit) {
    val state = collectShopState(vm)
    LaunchedEffect(Unit) { vm.loadFavourites() }
    if (state.favouritesLoading && state.favourites.isEmpty()) {
        LoadingState()
        return
    }
    if (state.favourites.isEmpty()) {
        EmptyState(
            "Keep your favourites close",
            "Tap the heart on a product to save it here.",
            "Refresh",
            {
                vm.loadFavourites()
            }
        )
        return
    }
    LazyVerticalGrid(
        columns = GridCells.Adaptive(155.dp),
        contentPadding = PaddingValues(16.dp),
        horizontalArrangement = Arrangement.spacedBy(12.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        items(state.favourites, key = { it.id }) { product ->
            ProductCard(
                product,
                cart.firstOrNull {
                    it.product.id == product.id
                }?.quantity ?: 0,
                { open(product.id) },
                { v, q -> vm.quantity(product, v, q) }
            )
        }
    }
}
