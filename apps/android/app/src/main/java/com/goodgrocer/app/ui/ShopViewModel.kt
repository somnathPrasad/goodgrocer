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
    val loading: Boolean = false,
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

class ShopViewModel(application: Application) : AndroidViewModel(application) {
    private val repository = Repository(application)
    val cart = repository.cart
    val signedIn = repository.signedIn
    private val _state = MutableStateFlow(ShopState())
    val state = _state.asStateFlow()
    private var searchJob: Job? = null
    private var requestKey: String = repository.requestKey()
    private var pending = 0
    private fun begin() {
        pending++
        change { it.copy(loading = true, error = null) }
    }
    private fun end() {
        pending--
        change { it.copy(loading = pending > 0) }
    }
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
        begin()
        try {
            block()
        } catch (
            error: CancellationException
        ) {
            throw error
        } catch (error: Exception) {
            failure(error)
        } finally {
            end()
        }
    }
    init {
        browse()
    }
    fun browse(query: String = "", category: Int? = null, append: Boolean = false) {
        searchJob?.cancel()
        searchJob = viewModelScope.launch {
            change {
                it.copy(
                    query = query,
                    category = category,
                    error = null,
                    products = if (append) it.products else emptyList()
                )
            }
            if (query.isNotEmpty() && !append) delay(350)
            begin()
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
                change {
                    it.copy(
                        products = if (append) it.products + result.items else result.items,
                        page = page,
                        total = result.total
                    )
                }
            } catch (
                error: CancellationException
            ) {
                throw error
            } catch (error: Exception) {
                failure(error)
            } finally {
                end()
            }
        }
    }
    fun loadProduct(id: Int) {
        change { it.copy(product = null) }
        task {
            val product = repository.api.product(id)
            change { it.copy(product = product) }
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
        }
    }
    fun loadAddresses() = task {
        val list = repository.api.addresses()
        change {
            it.copy(
                addresses = list,
                addressId =
                it.addressId?.takeIf { id -> list.any { a -> a.id == id } }
                    ?: list.firstOrNull()?.id
            )
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
    fun loadFavourites() = task {
        val list = repository.api.favourites()
        change { it.copy(favourites = list) }
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
    fun loadOrders(append: Boolean = false) = task {
        val page = if (append) {
            state.value.orderPage +
                1
        } else {
            1
        }
        val list = repository.api.orders(page)
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
    }
    fun loadOrder(id: Int, quiet: Boolean = false) {
        if (!quiet) {
            change { it.copy(order = null) }
            task {
                val order = repository.api.order(id)
                change { it.copy(order = order) }
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
