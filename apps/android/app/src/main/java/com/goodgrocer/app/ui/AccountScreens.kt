package com.goodgrocer.app.ui

import android.app.Activity
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.credentials.CredentialManager
import androidx.credentials.CustomCredential
import androidx.credentials.GetCredentialRequest
import androidx.credentials.exceptions.GetCredentialCancellationException
import androidx.credentials.exceptions.GetCredentialException
import com.goodgrocer.app.BuildConfig
import com.goodgrocer.app.data.Address
import com.google.android.libraries.identity.googleid.GetSignInWithGoogleOption
import com.google.android.libraries.identity.googleid.GoogleIdTokenCredential
import com.google.android.libraries.identity.googleid.GoogleIdTokenParsingException
import kotlinx.coroutines.launch

@Composable
fun LoginScreen(vm: ShopViewModel, done: () -> Unit) {
    val state = collectShopState(vm)
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var signInError by remember { mutableStateOf<String?>(null) }
    var pickingAccount by remember { mutableStateOf(false) }
    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(20.dp)
    ) {
        Text("Your neighbourhood.\nYour account.", style = MaterialTheme.typography.headlineLarge)
        Text(
            "Sign in to save favourites, manage addresses and place orders. Your contact phone is collected at checkout."
        )
        PrimaryButton("Sign in with Google", !state.actionLoading && !pickingAccount) {
            signInError = null
            if (BuildConfig.GOOGLE_WEB_CLIENT_ID.isBlank()) {
                signInError = "Google sign-in is not configured for this app."
            } else {
                pickingAccount = true
                scope.launch {
                    try {
                        val option = GetSignInWithGoogleOption.Builder(
                            BuildConfig.GOOGLE_WEB_CLIENT_ID
                        ).build()
                        val request = GetCredentialRequest.Builder().addCredentialOption(
                            option
                        ).build()
                        val credential = CredentialManager.create(
                            context
                        ).getCredential(context as Activity, request).credential
                        if (credential !is CustomCredential ||
                            credential.type !=
                            GoogleIdTokenCredential.TYPE_GOOGLE_ID_TOKEN_CREDENTIAL
                        ) {
                            signInError = "Choose a Google account to continue."
                        } else {
                            val token = GoogleIdTokenCredential.createFrom(credential.data).idToken
                            vm.googleSignIn(token, done)
                        }
                    } catch (_: GetCredentialCancellationException) {
                        // Dismissing the account picker leaves the customer on this screen.
                    } catch (_: GetCredentialException) {
                        signInError = "Google sign-in could not start. Please try again."
                    } catch (_: GoogleIdTokenParsingException) {
                        signInError =
                            "Google sign-in returned an unreadable account. Please try again."
                    } finally {
                        pickingAccount = false
                    }
                }
            }
        }
        signInError?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        if (state.actionLoading || pickingAccount) LinearProgressIndicator(Modifier.fillMaxWidth())
    }
}

@Composable
fun AccountScreen(signedIn: Boolean, login: () -> Unit, addresses: () -> Unit, logout: () -> Unit) {
    Column(Modifier.padding(24.dp), verticalArrangement = Arrangement.spacedBy(18.dp)) {
        SectionTitle("Your Goodgrocer", "Everyday shopping, a little easier.")
        if (!signedIn) {
            PrimaryButton("Sign in with Google", click = login)
        } else {
            PrimaryButton("Manage saved addresses", click = addresses)
            OutlinedButton(onClick = logout) { Text("Sign out") }
        }
    }
}

@Composable
fun AddressScreen(vm: ShopViewModel) {
    val state = collectShopState(vm)
    LaunchedEffect(Unit) { vm.loadAddresses() }
    var edit by remember { mutableStateOf<Address?>(null) }
    var delete by remember { mutableStateOf<Address?>(null) }
    if (edit !=
        null
    ) {
        AddressEditor(edit!!, state.addressesLoading || state.actionLoading, {
            vm.saveAddress(it) {
                edit =
                    null
            }
        }, {
            edit =
                null
        })
        return
    }
    LazyColumn(
        contentPadding = PaddingValues(20.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        item { PrimaryButton("+ Add address", click = { edit = Address() }) }
        if (state.addressesLoading) item { LinearProgressIndicator(Modifier.fillMaxWidth()) }
        if (!state.addressesLoading &&
            state.addresses.isEmpty()
        ) {
            item {
                EmptyState(
                    "Where should we deliver?",
                    "Save an address for a quicker checkout.",
                    "Refresh",
                    {
                        vm.loadAddresses()
                    }
                )
            }
        }
        items(state.addresses, key = { it.id!! }) { address ->
            Card(
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
            ) {
                Column(
                    Modifier.fillMaxWidth().padding(18.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Text(address.recipient_name, style = MaterialTheme.typography.titleMedium)
                    Text(
                        "${address.line1}\n${address.line2.orEmpty()} ${address.locality.orEmpty()}\n${address.city}, ${address.state} ${address.postal_code.orEmpty()}"
                    )
                    Text(address.phone)
                    Row {
                        TextButton(onClick = {
                            edit =
                                address
                        }) { Text("Edit") }
                        TextButton(onClick = { delete = address }) { Text("Delete") }
                    }
                }
            }
        }
    }
    delete?.let { address ->
        AlertDialog(onDismissRequest = {
            delete = null
        }, title = {
            Text("Delete this address?")
        }, text = { Text(address.line1) }, confirmButton = {
            TextButton(onClick = {
                vm.deleteAddress(address.id!!)
                delete =
                    null
            }) { Text("Delete") }
        }, dismissButton = { TextButton(onClick = { delete = null }) { Text("Keep") } })
    }
}

@Composable
fun AddressEditor(initial: Address, busy: Boolean, save: (Address) -> Unit, cancel: () -> Unit) {
    var name by rememberSaveable(initial.id) { mutableStateOf(initial.recipient_name) }
    var phone by rememberSaveable(initial.id) { mutableStateOf(initial.phone) }
    var line1 by rememberSaveable(initial.id) { mutableStateOf(initial.line1) }
    var line2 by rememberSaveable(initial.id) { mutableStateOf(initial.line2.orEmpty()) }
    var landmark by rememberSaveable(initial.id) { mutableStateOf(initial.landmark.orEmpty()) }
    var locality by rememberSaveable(initial.id) { mutableStateOf(initial.locality.orEmpty()) }
    var city by rememberSaveable(initial.id) { mutableStateOf(initial.city) }
    var region by rememberSaveable(initial.id) { mutableStateOf(initial.state) }
    var postal by rememberSaveable(initial.id) { mutableStateOf(initial.postal_code.orEmpty()) }
    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        SectionTitle(if (initial.id == null) "Add an address" else "Edit address")
        ShopField("Recipient name", name, { name = it })
        ShopField("Phone", phone, {
            phone = it
        }, keyboard = KeyboardOptions(keyboardType = KeyboardType.Phone))
        ShopField("House / street", line1, {
            line1 =
                it
        })
        ShopField("Address line 2 (optional)", line2, { line2 = it })
        ShopField("Landmark (optional)", landmark, {
            landmark =
                it
        })
        ShopField("Locality (optional)", locality, { locality = it })
        ShopField("City / town", city, {
            city =
                it
        })
        ShopField("State", region, { region = it })
        ShopField("Postal code (optional)", postal, {
            postal =
                it
        })
        PrimaryButton(
            "Save address",
            !busy &&
                listOf(name, phone, line1, city, region).all {
                    it.isNotBlank()
                }
        ) {
            save(
                initial.copy(
                    recipient_name = name, phone = phone, line1 = line1,
                    line2 = line2.ifBlank {
                        null
                    },
                    landmark = landmark.ifBlank {
                        null
                    },
                    locality = locality.ifBlank {
                        null
                    },
                    city = city, state = region, postal_code = postal.ifBlank { null }
                )
            )
        }
        TextButton(onClick = cancel) { Text("Cancel") }
    }
}
