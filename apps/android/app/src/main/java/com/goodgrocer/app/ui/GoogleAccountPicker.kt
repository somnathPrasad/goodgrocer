package com.goodgrocer.app.ui

import android.app.Activity
import androidx.credentials.CredentialManager
import androidx.credentials.CustomCredential
import androidx.credentials.GetCredentialRequest
import androidx.credentials.exceptions.NoCredentialException
import com.google.android.libraries.identity.googleid.GetGoogleIdOption
import com.google.android.libraries.identity.googleid.GetSignInWithGoogleOption
import com.google.android.libraries.identity.googleid.GoogleIdTokenCredential

suspend fun pickGoogleAccount(activity: Activity, clientId: String): GoogleIdTokenCredential {
    val manager = CredentialManager.create(activity)
    val googleOption = GetGoogleIdOption.Builder()
        .setServerClientId(clientId)
        .setFilterByAuthorizedAccounts(false)
        .setAutoSelectEnabled(false)
        .build()
    val credential = try {
        manager.getCredential(
            activity,
            GetCredentialRequest.Builder().addCredentialOption(googleOption).build()
        ).credential
    } catch (_: NoCredentialException) {
        manager.getCredential(
            activity,
            GetCredentialRequest.Builder()
                .addCredentialOption(GetSignInWithGoogleOption.Builder(clientId).build())
                .build()
        ).credential
    }
    if (
        credential !is CustomCredential ||
        credential.type != GoogleIdTokenCredential.TYPE_GOOGLE_ID_TOKEN_CREDENTIAL
    ) {
        throw IllegalStateException("Google did not return an ID token")
    }
    return GoogleIdTokenCredential.createFrom(credential.data)
}
