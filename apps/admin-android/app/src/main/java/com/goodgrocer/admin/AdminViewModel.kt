package com.goodgrocer.admin

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import java.math.BigDecimal
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import retrofit2.HttpException

data class AdminState(
    val signedIn: Boolean? = null,
    val section: String = "Dashboard",
    val busy: Boolean = false,
    val error: String = "",
    val notice: String = "",
    val dashboard: Dashboard? = null,
    val orders: List<Order> = emptyList(),
    val products: ProductPage? = null,
    val brands: List<Brand> = emptyList(),
    val categories: List<Category> = emptyList(),
    val page: Int = 1,
    val query: String = "",
    val status: String = "",
    val category: Int? = null,
    val availability: Boolean? = null,
    val selectedOrder: Order? = null,
    val selectedProduct: Product? = null
)

class AdminViewModel(application: Application) : AndroidViewModel(application) {
    val repo = AdminRepository(application)
    private val _state = MutableStateFlow(AdminState())
    val state = _state.asStateFlow()
    private var activeOperations = 0
    private var loadGeneration = 0
    init {
        viewModelScope.launch {
            if (repo.hasSession()) {
                try { repo.api.me(); _state.update { it.copy(signedIn = true) }; refresh() }
                catch (_: Exception) { repo.saveSession(null); _state.update { it.copy(signedIn = false) } }
            } else _state.update { it.copy(signedIn = false) }
        }
        viewModelScope.launch {
            while (true) {
                delay(30_000)
                if (state.value.signedIn == true && state.value.section in listOf("Dashboard", "Orders")) refresh()
            }
        }
    }
    private fun run(done: (() -> Unit)? = null, block: suspend () -> Unit) {
        viewModelScope.launch {
            activeOperations += 1
            _state.update { it.copy(busy = true, error = "", notice = "") }
            try { block(); done?.invoke() }
            catch (e: Exception) {
                if (e is HttpException && e.code() == 401) {
                    repo.saveSession(null)
                    _state.update { it.copy(signedIn = false) }
                }
                _state.update { it.copy(error = e.message ?: "Request failed") }
            } finally {
                activeOperations -= 1
                _state.update { it.copy(busy = activeOperations > 0) }
            }
        }
    }
    fun login(username: String, password: String) = run {
        val token = repo.api.login(LoginRequest(username, password))
        repo.saveSession(token.token)
        _state.update { it.copy(signedIn = true) }
        load()
    }
    fun logout() = run {
        try { repo.api.logout() } finally {
            repo.saveSession(null)
            _state.value = AdminState(signedIn = false)
        }
    }
    fun section(name: String) { _state.update { it.copy(section = name, page = 1) }; refresh() }
    fun page(value: Int) { _state.update { it.copy(page = value.coerceAtLeast(1)) }; refresh() }
    fun query(value: String) { _state.update { it.copy(query = value, page = 1) }; refresh() }
    fun status(value: String) { _state.update { it.copy(status = value, page = 1) }; refresh() }
    fun category(value: Int?) { _state.update { it.copy(category = value, page = 1) }; refresh() }
    fun availability(value: Boolean?) { _state.update { it.copy(availability = value, page = 1) }; refresh() }
    fun refresh() = run { load() }
    private suspend fun load() {
        val generation = ++loadGeneration
        val s = state.value
        val brands = repo.api.brands()
        val categories = repo.api.categories()
        if (generation != loadGeneration) return
        _state.update { it.copy(brands = brands, categories = categories) }
        when (s.section) {
            "Dashboard" -> {
                val dashboard = repo.api.dashboard()
                if (generation == loadGeneration) _state.update { it.copy(dashboard = dashboard) }
            }
            "Orders" -> {
                val orders = repo.api.orders(s.page, s.status.ifBlank { null })
                if (generation == loadGeneration) _state.update { it.copy(orders = orders) }
            }
            "Products" -> {
                val products = repo.api.products(s.page, s.query.ifBlank { null }, s.category, s.availability)
                if (generation == loadGeneration) _state.update { it.copy(products = products) }
            }
        }
    }
    fun openOrder(id: Int) = run {
        val order = repo.api.order(id)
        _state.update { it.copy(selectedOrder = order) }
    }
    fun closeOrder() { _state.update { it.copy(selectedOrder = null) } }
    fun transition(status: String, reason: String?, done: () -> Unit) = run(done) {
        val id = state.value.selectedOrder?.id ?: return@run
        val order = repo.api.status(id, StatusInput(status, reason))
        _state.update { it.copy(selectedOrder = order) }
        load()
    }
    fun markPaid(done: () -> Unit) = run(done) {
        val id = state.value.selectedOrder?.id ?: return@run
        val order = repo.api.markPaid(id)
        _state.update { it.copy(selectedOrder = order) }
        load()
    }
    fun openProduct(id: Int) = run {
        val product = repo.api.product(id)
        _state.update { it.copy(selectedProduct = product) }
    }
    fun closeProduct() { _state.update { it.copy(selectedProduct = null) } }
    fun saveBrand(id: Int?, input: BrandInput, done: () -> Unit) = run(done) {
        if (id == null) repo.api.createBrand(input) else repo.api.editBrand(id, input)
        load()
        _state.update { it.copy(notice = "Brand saved") }
    }
    fun saveCategory(id: Int?, input: CategoryInput, done: () -> Unit) = run(done) {
        if (id == null) repo.api.createCategory(input) else repo.api.editCategory(id, input)
        load()
        _state.update { it.copy(notice = "Category saved") }
    }
    fun saveProduct(id: Int?, input: ProductInput, done: () -> Unit) = run(done) {
        val product = if (id == null) repo.api.createProduct(input) else repo.api.editProduct(id, input)
        _state.update { it.copy(selectedProduct = product) }
        load()
        _state.update { it.copy(notice = "Product saved") }
    }
    fun saveVariant(productId: Int, variantId: Int?, input: VariantInput, done: () -> Unit) = run(done) {
        require(input.mrp.toBigDecimal() >= input.selling_price.toBigDecimal()) { "Selling price cannot exceed MRP" }
        require(input.selling_price.toBigDecimal() >= BigDecimal.ZERO) { "Price cannot be negative" }
        if (variantId == null) repo.api.createVariant(productId, input) else repo.api.editVariant(productId, variantId, input)
        val product = repo.api.product(productId)
        _state.update { it.copy(selectedProduct = product) }
        load()
        _state.update { it.copy(notice = "Variant saved") }
    }
    fun upload(bytes: ByteArray, mime: String, done: (String) -> Unit) = run {
        require(bytes.size <= 5 * 1024 * 1024) { "Choose an image under 5 MB" }
        done(repo.api.upload(repo.imagePart(bytes, mime)).image_url)
    }
}
