package com.goodgrocer.app.data

import android.content.Context
import com.goodgrocer.app.BuildConfig
import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import java.util.concurrent.TimeUnit
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory

class Repository(context: Context) {
    private val moshi = Moshi.Builder().addLast(KotlinJsonAdapterFactory()).build()
    private val local = LocalStore(context, moshi)
    private val _cart = MutableStateFlow(local.cart())
    val cart = _cart.asStateFlow()
    private val _signedIn = MutableStateFlow(local.token() != null)
    val signedIn = _signedIn.asStateFlow()
    private val http = OkHttpClient.Builder().connectTimeout(
        15,
        TimeUnit.SECONDS
    ).readTimeout(20, TimeUnit.SECONDS).addInterceptor { chain ->
        val request = chain.request().newBuilder()
        local.token()?.let { request.header("Authorization", "Bearer $it") }
        val response = chain.proceed(request.build())
        if (response.code == 401) {
            local.saveToken(null)
            _signedIn.value = false
        }
        response
    }.build()
    val api: Api = Retrofit.Builder().baseUrl(
        BuildConfig.API_URL
    ).client(
        http
    ).addConverterFactory(MoshiConverterFactory.create(moshi)).build().create(Api::class.java)
    fun requestKey(): String = local.requestKey()
    fun newRequestKey(): String = local.newRequestKey()
    fun quantity(product: Product, variant: Variant, quantity: Int) {
        replaceCart(updateQuantity(cart.value, product, variant, quantity))
    }
    fun replaceCart(lines: List<CartLine>) {
        local.saveCart(lines)
        _cart.value = lines
    }
    fun signIn(token: String) {
        local.saveToken(token)
        _signedIn.value = true
    }
    fun clearSession() {
        local.saveToken(null)
        _signedIn.value = false
    }
    fun clearCustomerData() {
        local.clearAll()
        _cart.value = emptyList()
        _signedIn.value = false
    }
}
