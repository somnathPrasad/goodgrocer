package com.goodgrocer.app.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.goodgrocer.app.data.Address
import com.goodgrocer.app.data.CartItem
import com.goodgrocer.app.data.CartLine
import com.goodgrocer.app.data.Category
import com.goodgrocer.app.data.CheckoutRequest
import com.goodgrocer.app.data.Order
import com.goodgrocer.app.data.OrderRequest
import com.goodgrocer.app.data.OtpResult
import com.goodgrocer.app.data.PhoneRequest
import com.goodgrocer.app.data.Product
import com.goodgrocer.app.data.Quote
import com.goodgrocer.app.data.Repository
import com.goodgrocer.app.data.StoreConfig
import com.goodgrocer.app.data.Variant
import com.goodgrocer.app.data.VerifyRequest
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import org.json.JSONObject
import retrofit2.HttpException

data class ShopState(
    val catalogueLoading: Boolean = false,
    val productLoading: Boolean = false,
    val favouritesLoading: Boolean = false,
    val addressesLoading: Boolean = false,
    val ordersLoading: Boolean = false,
    val orderLoading: Boolean = false,
    val actionLoading: Boolean = false,
    val error: String? = null,
    val message: String? = null,
    val products: List<Product> = emptyList(),
    val categories: List<Category> = emptyList(),
    val total: Int = 0,
    val page: Int = 1,
    val query: String = "",
    val category: Int? = null,
    val product: Product? = null,
    val favourites: List<Product> = emptyList(),
    val addresses: List<Address> = emptyList(),
    val orders: List<Order> = emptyList(),
    val orderPage: Int = 1,
    val moreOrders: Boolean = false,
    val order: Order? = null,
    val quote: Quote? = null,
    val otp: OtpResult? = null,
    val config: StoreConfig? = null,
    val fulfilment: String = "DELIVERY",
    val payment: String = "COD",
    val addressId: Int? = null
)

private data class CatalogueCache(
    val products: List<Product>,
    val total: Int,
    val page: Int,
    val refreshedAt: Long
)

class ShopViewModel(application: Application) : AndroidViewModel(application) {
    private val repository = Repository(application)
    val cart = repository.cart
    val signedIn = repository.signedIn
    private val _state = MutableStateFlow(ShopState())
    val state = _state.asStateFlow()
    private var searchJob: Job? = null
    private var browseGeneration = 0L
    private var productJob: Job? = null
    private var productGeneration = 0L
    private var requestKey: String = repository.requestKey()
    private val catalogueCache = mutableMapOf<String, CatalogueCache>()
    private val productCache = mutableMapOf<Int, Product>()
    private val favouritesCache = mutableListOf<Product>()
    private val addressesCache = mutableListOf<Address>()
    private val ordersCache = mutableListOf<Order>()
    private val orderCache = mutableMapOf<Int, Order>()
    private var favouritesLoaded = false
    private var addressesLoaded = false
    private var ordersLoaded = false
    private val refreshWindowMs = 60_000L

    private fun begin(setLoading: (ShopState) -> ShopState) {
        change { setLoading(it).copy(error = null) }
    }
    private fun end(setLoading: (ShopState) -> ShopState) {
        change(setLoading)
    }
    private fun actionBegin() = begin { it.copy(actionLoading = true) }
    private fun actionEnd() = end { it.copy(actionLoading = false) }
    private fun change(block: (ShopState) -> ShopState) {
        _state.value = block(_state.value)
    }
    fun clearMessage() = change { it.copy(error = null, message = null) }
    private fun failure(error: Exception) {
        val message = if (error is HttpException) {
            runCatching {
                JSONObject(
                    error.response()?.errorBody()?.string() ?: "{}"
                ).getJSONObject("error").getString("message")
            }.getOrDefault("Please try again.")
        } else {
            "Cannot reach your store. Check your connection and try again."
        }
        change { it.copy(error = message) }
    }
    private fun task(block: suspend () -> Unit) = viewModelScope.launch {
        actionBegin()
        try {
            block()
        } catch (
            error: CancellationException
        ) {
            throw error
        } catch (error: Exception) {
            failure(error)
        } finally {
            actionEnd()
        }
    }
    fun browse(query: String = "", category: Int? = null, append: Boolean = false) {
        searchJob?.cancel()
        val generation = ++browseGeneration
        searchJob = viewModelScope.launch {
            val key = "$query|${category ?: "all"}"
            val cached = catalogueCache[key]
            change {
                it.copy(
                    query = query,
                    category = category,
                    error = null,
                    products = if (append) it.products else cached?.products
                        ?: if (query.isNotEmpty()) it.products else emptyList(),
                    total = cached?.total ?: it.total,
                    page = cached?.page ?: 1
                )
            }
            if (!append && cached != null && System.currentTimeMillis() - cached.refreshedAt < refreshWindowMs) {
                return@launch
            }
            if (query.isNotEmpty() && !append) delay(350)
            begin { it.copy(catalogueLoading = true) }
            try {
                if (state.value.config == null ||
                    (query.isEmpty() && category == null && !append)
                ) {
                    val config = repository.api.config()
                    val categories = repository.api.categories()
                    change { it.copy(config = config, categories = categories) }
                }
                val page = if (append) state.value.page + 1 else 1
                val result = repository.api.products(query.ifBlank { null }, category, page)
                if (generation != browseGeneration) return@launch
                change {
                    it.copy(
                        products = if (append) it.products + result.items else result.items,
                        page = page,
                        total = result.total
                    )
                }
                catalogueCache[key] = CatalogueCache(
                    if (append) state.value.products else result.items,
                    result.total,
                    page,
                    System.currentTimeMillis()
                )
                result.items.forEach { productCache[it.id] = it }
            } catch (
                error: CancellationException
            ) {
                throw error
            } catch (error: Exception) {
                failure(error)
            } finally {
                if (generation == browseGeneration) {
                    end { it.copy(catalogueLoading = false) }
                }
            }
        }
    }
    fun loadProduct(id: Int) {
        productJob?.cancel()
        val generation = ++productGeneration
        change { it.copy(product = productCache[id]) }
        productJob = viewModelScope.launch {
            begin { it.copy(productLoading = true) }
            try {
                val product = repository.api.product(id)
                if (generation != productGeneration) return@launch
                productCache[id] = product
                change { it.copy(product = product) }
            } catch (error: CancellationException) {
                throw error
            } catch (error: Exception) {
                failure(error)
            } finally {
                if (generation == productGeneration) {
                    end { it.copy(productLoading = false) }
                }
            }
        }
    }
    fun quantity(product: Product, variant: Variant, quantity: Int) {
        repository.quantity(product, variant, quantity)
        invalidateQuote()
    }
    private fun invalidateQuote() {
        requestKey = repository.newRequestKey()
        change { it.copy(quote = null) }
    }
    fun checkoutOptions(
        fulfilment: String = state.value.fulfilment,
        payment: String = state.value.payment,
        addressId: Int? = state.value.addressId
    ) {
        change { it.copy(fulfilment = fulfilment, payment = payment, addressId = addressId) }
        invalidateQuote()
    }
    fun requestOtp(phone: String) = task {
        change { it.copy(otp = null) }
        val result = repository.api.requestOtp(PhoneRequest(phone))
        change { it.copy(otp = result) }
    }
    fun verifyOtp(phone: String, code: String, done: () -> Unit) = task {
        repository.signIn(repository.api.verifyOtp(VerifyRequest(phone, code)).token)
        change { it.copy(otp = null) }
        done()
    }
    fun logout() = task {
        try {
            repository.api.logout()
        } finally {
            repository.clearSession()
            change {
                it.copy(
                    addresses = emptyList(),
                    favourites = emptyList(),
                    orders = emptyList(),
                    order = null,
                    quote = null,
                    addressId = null
                )
            }
            favouritesCache.clear()
            addressesCache.clear()
            ordersCache.clear()
            orderCache.clear()
            favouritesLoaded = false
            addressesLoaded = false
            ordersLoaded = false
        }
    }
    fun loadAddresses() = viewModelScope.launch {
        if (addressesLoaded) change { it.copy(addresses = addressesCache.toList()) }
        begin { it.copy(addressesLoading = true) }
        try {
        val list = repository.api.addresses()
        addressesCache.apply { clear(); addAll(list) }
        addressesLoaded = true
        change {
            it.copy(
                addresses = list,
                addressId =
                it.addressId?.takeIf { id -> list.any { a -> a.id == id } }
                    ?: list.firstOrNull()?.id
            )
        }
        } catch (error: CancellationException) {
            throw error
        } catch (error: Exception) {
            failure(error)
        } finally {
            end { it.copy(addressesLoading = false) }
        }
    }
    fun saveAddress(address: Address, done: () -> Unit) = task {
        if (address.id ==
            null
        ) {
            repository.api.createAddress(address)
        } else {
            repository.api.editAddress(address.id, address.copy(id = null))
        }
        val list = repository.api.addresses()
        change {
            it.copy(
                addresses = list,
                addressId =
                it.addressId ?: list.lastOrNull()?.id
            )
        }
        invalidateQuote()
        done()
    }
    fun deleteAddress(id: Int) = task {
        repository.api.deleteAddress(id)
        val list = repository.api.addresses()
        change {
            it.copy(
                addresses = list,
                addressId = if (it.addressId ==
                    id
                ) {
                    null
                } else {
                    it.addressId
                }
            )
        }
        invalidateQuote()
    }
    fun loadFavourites() = viewModelScope.launch {
        if (favouritesLoaded) change { it.copy(favourites = favouritesCache.toList()) }
        begin { it.copy(favouritesLoading = true) }
        try {
        val list = repository.api.favourites()
        favouritesCache.apply { clear(); addAll(list) }
        favouritesLoaded = true
        change { it.copy(favourites = list) }
        } catch (error: CancellationException) {
            throw error
        } catch (error: Exception) {
            failure(error)
        } finally {
            end { it.copy(favouritesLoading = false) }
        }
    }
    fun favourite(product: Product) = task {
        if (state.value.favourites.any {
                it.id == product.id
            }
        ) {
            repository.api.unfavourite(product.id)
        } else {
            repository.api.favourite(product.id)
        }
        val list = repository.api.favourites()
        change { it.copy(favourites = list, message = "Favourites updated") }
    }
    private fun checkout() = CheckoutRequest(
        cart.value.map {
            CartItem(it.variant.id, it.quantity)
        },
        state.value.fulfilment,
        state.value.payment,
        if (state.value.fulfilment ==
            "DELIVERY"
        ) {
            state.value.addressId
        } else {
            null
        }
    )
    fun reviewQuote() = task {
        val quote = repository.api.quote(checkout())
        change { it.copy(quote = quote) }
    }
    fun placeOrder(done: (Int) -> Unit) = task {
        val quote = state.value.quote ?: return@task
        val request = checkout()
        try {
            val order = repository.api.place(
                OrderRequest(
                    request.items,
                    request.fulfilment_type,
                    request.payment_method,
                    request.address_id,
                    quote.quote_token,
                    requestKey
                )
            )
            repository.replaceCart(emptyList())
            change { it.copy(order = order, quote = null) }
            requestKey =
                repository.newRequestKey()
            done(order.id)
        } catch (error: HttpException) {
            if (error.code() == 409) invalidateQuote()
            throw error
        }
    }
    fun loadOrders(append: Boolean = false) = viewModelScope.launch {
        if (!append && ordersLoaded) change { it.copy(orders = ordersCache.toList()) }
        begin { it.copy(ordersLoading = true) }
        try {
        val page = if (append) {
            state.value.orderPage +
                1
        } else {
            1
        }
        val list = repository.api.orders(page)
        if (!append) ordersCache.apply { clear(); addAll(list) } else ordersCache.addAll(list)
        if (!append) ordersLoaded = true
        list.forEach { orderCache[it.id] = it }
        change {
            it.copy(
                orders = if (append) {
                    it.orders +
                        list
                } else {
                    list
                },
                orderPage = page,
                moreOrders = list.size == 20
            )
        }
        } catch (error: CancellationException) {
            throw error
        } catch (error: Exception) {
            failure(error)
        } finally {
            end { it.copy(ordersLoading = false) }
        }
    }
    fun loadOrder(id: Int, quiet: Boolean = false) {
        if (!quiet) {
            change { it.copy(order = orderCache[id]) }
            viewModelScope.launch {
                begin { it.copy(orderLoading = true) }
                try {
                val order = repository.api.order(id)
                orderCache[id] = order
                change { it.copy(order = order) }
                } catch (error: CancellationException) {
                    throw error
                } catch (error: Exception) {
                    failure(error)
                } finally {
                    end { it.copy(orderLoading = false) }
                }
            }
        } else {
            viewModelScope.launch {
                try {
                    val order = repository.api.order(id)
                    change { it.copy(order = order) }
                } catch (
                    error: CancellationException
                ) {
                    throw error
                } catch (error: Exception) {
                    failure(error)
                }
            }
        }
    }
    fun reorder(id: Int, done: () -> Unit) = task {
        val result = repository.api.reorder(id)
        val lines = result.items.mapNotNull { item ->
            result.products.firstOrNull { p ->
                p.variants.any {
                    it.id ==
                        item.variant_id
                }
            }?.let { p ->
                CartLine(p, p.variants.first { it.id == item.variant_id }, item.quantity)
            }
        }
        repository.replaceCart(lines)
        invalidateQuote()
        change {
            it.copy(
                message = if (result.unavailable.isEmpty()) {
                    "Cart updated with today’s prices"
                } else {
                    "Unavailable items skipped: ${result.unavailable.joinToString()}"
                }
            )
        }
        done()
    }
    fun developmentPayment(id: Int, outcome: String) = task {
        val order = repository.api.developmentPayment(id, outcome)
        change { it.copy(order = order) }
    }
}
