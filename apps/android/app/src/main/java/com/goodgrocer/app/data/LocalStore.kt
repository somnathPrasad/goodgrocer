package com.goodgrocer.app.data

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import com.squareup.moshi.Moshi
import com.squareup.moshi.Types
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

class LocalStore(context: Context, moshi: Moshi) {
    private val prefs = context.getSharedPreferences("goodgrocer", Context.MODE_PRIVATE)
    private val cartAdapter = moshi.adapter<List<CartLine>>(
        Types.newParameterizedType(List::class.java, CartLine::class.java)
    )
    fun cart(): List<CartLine> = runCatching {
        cartAdapter.fromJson(prefs.getString("cart", "[]")!!)
            ?: emptyList()
    }.getOrDefault(emptyList())
    fun saveCart(lines: List<CartLine>) {
        prefs.edit().putString("cart", cartAdapter.toJson(lines)).apply()
    }
    fun requestKey(): String = prefs.getString("request_key", null) ?: newRequestKey()
    fun newRequestKey(): String = java.util.UUID.randomUUID().toString().also {
        prefs.edit().putString("request_key", it).apply()
    }
    private fun key(): SecretKey {
        val store = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        (store.getKey("gg-session", null) as? SecretKey)?.let { return it }
        return KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore").apply {
            init(
                KeyGenParameterSpec.Builder(
                    "gg-session",
                    KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
                ).setBlockModes(
                    KeyProperties.BLOCK_MODE_GCM
                ).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build()
            )
        }.generateKey()
    }
    fun token(): String? = runCatching {
        val encoded = prefs.getString("session", null) ?: return null
        val parts = encoded.split(":")
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(
            Cipher.DECRYPT_MODE,
            key(),
            GCMParameterSpec(128, Base64.decode(parts[0], Base64.NO_WRAP))
        )
        String(cipher.doFinal(Base64.decode(parts[1], Base64.NO_WRAP)), Charsets.UTF_8)
    }.getOrNull()
    fun saveToken(token: String?) {
        if (token == null) {
            prefs.edit().remove("session").apply()
            return
        }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, key())
        prefs.edit().putString(
            "session",
            Base64.encodeToString(cipher.iv, Base64.NO_WRAP) + ":" +
                Base64.encodeToString(cipher.doFinal(token.toByteArray()), Base64.NO_WRAP)
        ).apply()
    }
}
