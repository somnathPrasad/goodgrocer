package com.goodgrocer.app.data

import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Path
import retrofit2.http.Query

interface Api {
    @GET("api/v1/config")
    suspend fun config(): StoreConfig

    @GET("api/v1/categories")
    suspend fun categories(): List<Category>

    @GET("api/v1/products")
    suspend fun products(
        @Query("q") query: String? = null,
        @Query("category_id") category: Int? = null,
        @Query("page") page: Int = 1
    ): ProductPage

    @GET("api/v1/products/{id}")
    suspend fun product(@Path("id") id: Int): Product

    @POST("api/v1/auth/google")
    suspend fun googleLogin(@Body request: GoogleLoginRequest): AuthToken

    @POST("api/v1/auth/logout")
    suspend fun logout()

    @GET("api/v1/addresses")
    suspend fun addresses(): List<Address>

    @POST("api/v1/addresses")
    suspend fun createAddress(@Body address: Address): Address

    @PUT("api/v1/addresses/{id}")
    suspend fun editAddress(@Path("id") id: Int, @Body address: Address): Address

    @DELETE("api/v1/addresses/{id}")
    suspend fun deleteAddress(@Path("id") id: Int)

    @GET("api/v1/favourites")
    suspend fun favourites(): List<Product>

    @PUT("api/v1/favourites/{id}")
    suspend fun favourite(@Path("id") id: Int)

    @DELETE("api/v1/favourites/{id}")
    suspend fun unfavourite(@Path("id") id: Int)

    @POST("api/v1/checkout/quote")
    suspend fun quote(@Body request: CheckoutRequest): Quote

    @POST("api/v1/orders")
    suspend fun place(@Body request: OrderRequest): Order

    @GET("api/v1/orders")
    suspend fun orders(@Query("page") page: Int = 1): List<Order>

    @GET("api/v1/orders/{id}")
    suspend fun order(@Path("id") id: Int): Order

    @POST("api/v1/orders/{id}/reorder")
    suspend fun reorder(@Path("id") id: Int): ReorderResult

    @POST("api/v1/orders/{id}/development-payment")
    suspend fun developmentPayment(@Path("id") id: Int, @Query("outcome") outcome: String): Order
}
