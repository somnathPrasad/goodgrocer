package com.goodgrocer.admin

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec
import okhttp3.Interceptor
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.RequestBody.Companion.toRequestBody
import retrofit2.Retrofit
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Part
import retrofit2.http.Path
import retrofit2.http.Query

data class LoginRequest(val username: String, val password: String)
data class TokenResponse(val token: String, val expires_at: String)
data class Brand(val id: Int, val name: String, val slug: String, val active: Boolean)
data class BrandInput(val name: String, val slug: String, val active: Boolean)
data class Category(val id: Int, val name: String, val slug: String, val active: Boolean, val image_url: String?, val display_order: Int)
data class CategoryInput(val name: String, val slug: String, val active: Boolean, val image_url: String?, val display_order: Int)
data class Variant(val id: Int, val name: String, val mrp: String, val selling_price: String, val active: Boolean, val available: Boolean, val display_order: Int)
data class VariantInput(val name: String, val mrp: String, val selling_price: String, val active: Boolean, val available: Boolean, val display_order: Int)
data class Product(val id: Int, val name: String, val slug: String, val description: String, val image_url: String?, val active: Boolean, val available: Boolean, val brand_id: Int, val brand: Brand, val categories: List<Category>, val variants: List<Variant>)
data class ProductInput(val name: String, val slug: String, val description: String, val image_url: String?, val active: Boolean, val available: Boolean, val brand_id: Int, val category_ids: List<Int>)
data class ProductPage(val items: List<Product>, val total: Int, val page: Int, val page_size: Int)
data class OrderItem(val product_name: String, val variant_name: String, val quantity: Int, val line_total: String)
data class Order(val id: Int, val order_number: String, val customer_phone: String, val fulfilment_type: String, val status: String, val payment_method: String, val payment_status: String, val total: String, val created_at: String, val address_snapshot: Map<String, Any?>?, val cancellation_reason: String?, val items: List<OrderItem>)
data class Dashboard(val awaiting_action: Int, val today_orders: Int, val unavailable_products: Int, val recent_orders: List<Order>)
data class StatusInput(val status: String, val reason: String? = null)
data class ImageResult(val image_url: String)

interface AdminApi {
    @POST("api/v1/admin/auth/mobile-login") suspend fun login(@Body input: LoginRequest): TokenResponse
    @POST("api/v1/admin/auth/logout") suspend fun logout()
    @GET("api/v1/admin/me") suspend fun me(): Map<String, Boolean>
    @GET("api/v1/admin/dashboard") suspend fun dashboard(): Dashboard
    @GET("api/v1/admin/orders") suspend fun orders(@Query("page") page: Int, @Query("status") status: String?): List<Order>
    @GET("api/v1/admin/orders/{id}") suspend fun order(@Path("id") id: Int): Order
    @POST("api/v1/admin/orders/{id}/status") suspend fun status(@Path("id") id: Int, @Body input: StatusInput): Order
    @POST("api/v1/admin/orders/{id}/mark-paid") suspend fun markPaid(@Path("id") id: Int): Order
    @GET("api/v1/admin/brands") suspend fun brands(): List<Brand>
    @POST("api/v1/admin/brands") suspend fun createBrand(@Body input: BrandInput): Brand
    @PUT("api/v1/admin/brands/{id}") suspend fun editBrand(@Path("id") id: Int, @Body input: BrandInput): Brand
    @GET("api/v1/admin/categories") suspend fun categories(): List<Category>
    @POST("api/v1/admin/categories") suspend fun createCategory(@Body input: CategoryInput): Category
    @PUT("api/v1/admin/categories/{id}") suspend fun editCategory(@Path("id") id: Int, @Body input: CategoryInput): Category
    @GET("api/v1/admin/products") suspend fun products(@Query("page") page: Int, @Query("q") query: String?, @Query("category_id") category: Int?, @Query("available") available: Boolean?): ProductPage
    @GET("api/v1/admin/products/{id}") suspend fun product(@Path("id") id: Int): Product
    @POST("api/v1/admin/products") suspend fun createProduct(@Body input: ProductInput): Product
    @PUT("api/v1/admin/products/{id}") suspend fun editProduct(@Path("id") id: Int, @Body input: ProductInput): Product
    @POST("api/v1/admin/products/{id}/variants") suspend fun createVariant(@Path("id") id: Int, @Body input: VariantInput): Variant
    @PUT("api/v1/admin/products/{id}/variants/{variantId}") suspend fun editVariant(@Path("id") id: Int, @Path("variantId") variantId: Int, @Body input: VariantInput): Variant
    @Multipart @POST("api/v1/admin/images") suspend fun upload(@Part file: MultipartBody.Part): ImageResult
}

class SessionStore(context: Context) {
    private val prefs = context.getSharedPreferences("admin_session", Context.MODE_PRIVATE)
    private fun key(): SecretKey {
        val store = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        (store.getKey("gg-admin-session", null) as? SecretKey)?.let { return it }
        return KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore").apply {
            init(KeyGenParameterSpec.Builder("gg-admin-session", KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build())
        }.generateKey()
    }
    fun token(): String? = runCatching {
        val parts = (prefs.getString("token", null) ?: return null).split(":")
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.DECRYPT_MODE, key(), GCMParameterSpec(128, Base64.decode(parts[0], Base64.NO_WRAP)))
        String(cipher.doFinal(Base64.decode(parts[1], Base64.NO_WRAP)), Charsets.UTF_8)
    }.getOrNull()
    fun save(token: String?) {
        if (token == null) { prefs.edit().remove("token").apply(); return }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, key())
        prefs.edit().putString("token", Base64.encodeToString(cipher.iv, Base64.NO_WRAP) + ":" +
            Base64.encodeToString(cipher.doFinal(token.toByteArray()), Base64.NO_WRAP)).apply()
    }
}

class AdminRepository(context: Context) {
    private val session = SessionStore(context)
    val api: AdminApi = Retrofit.Builder().baseUrl(BuildConfig.API_URL)
        .client(OkHttpClient.Builder().addInterceptor(Interceptor { chain ->
            val request = chain.request().newBuilder()
            session.token()?.let { request.header("Authorization", "Bearer $it") }
            chain.proceed(request.build())
        }).build())
        .addConverterFactory(retrofit2.converter.moshi.MoshiConverterFactory.create(
            Moshi.Builder().addLast(KotlinJsonAdapterFactory()).build()
        )).build().create(AdminApi::class.java)
    fun hasSession() = session.token() != null
    fun saveSession(token: String?) = session.save(token)
    fun imagePart(bytes: ByteArray, mime: String): MultipartBody.Part = MultipartBody.Part.createFormData(
        "file", "catalogue-image", bytes.toRequestBody(mime.toMediaType())
    )
}
