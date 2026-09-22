package com.goodgrocer.app.ui

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
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.goodgrocer.app.BuildConfig
import com.goodgrocer.app.data.Address
import com.goodgrocer.app.data.AddressSuggestion
import com.google.android.gms.maps.model.LatLng

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
        AddressEditor(edit!!, state.addressesLoading || state.actionLoading, vm::reverseGeocode, {
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
fun AddressEditor(
    initial: Address,
    busy: Boolean,
    lookup: (String, String, (AddressSuggestion?) -> Unit) -> Unit,
    save: (Address) -> Unit,
    cancel: () -> Unit
) {
    var name by rememberSaveable(initial.id) { mutableStateOf(initial.recipient_name) }
    var phone by rememberSaveable(initial.id) { mutableStateOf(initial.phone) }
    var line1 by rememberSaveable(initial.id) { mutableStateOf(initial.line1) }
    var line2 by rememberSaveable(initial.id) { mutableStateOf(initial.line2.orEmpty()) }
    var landmark by rememberSaveable(initial.id) { mutableStateOf(initial.landmark.orEmpty()) }
    var locality by rememberSaveable(initial.id) { mutableStateOf(initial.locality.orEmpty()) }
    var city by rememberSaveable(initial.id) { mutableStateOf(initial.city) }
    var region by rememberSaveable(initial.id) { mutableStateOf(initial.state) }
    var postal by rememberSaveable(initial.id) { mutableStateOf(initial.postal_code.orEmpty()) }
    var latitude by rememberSaveable(initial.id) { mutableStateOf(initial.latitude) }
    var longitude by rememberSaveable(initial.id) { mutableStateOf(initial.longitude) }
    var showMap by rememberSaveable(initial.id) {
        mutableStateOf(BuildConfig.MAPS_ENABLED && initial.id == null)
    }
    var moreDetails by rememberSaveable(initial.id) { mutableStateOf(false) }
    var lookupMessage by remember { mutableStateOf<String?>(null) }
    if (showMap) {
        MapPinPicker(
            initial = LatLng(
                latitude?.toDoubleOrNull() ?: BuildConfig.STORE_LATITUDE,
                longitude?.toDoubleOrNull() ?: BuildConfig.STORE_LONGITUDE
            ),
            confirm = { point ->
                latitude = point.latitude.toString()
                longitude = point.longitude.toString()
                showMap = false
                lookupMessage = "Looking up the pinned area…"
                lookup(latitude!!, longitude!!) { suggestion ->
                    if (suggestion == null) {
                        lookupMessage = "Could not suggest an address. Enter the details below."
                    } else {
                        if (suggestion.line1.isNotBlank()) line1 = suggestion.line1
                        locality = suggestion.locality
                        city = suggestion.city
                        region = suggestion.state
                        postal = suggestion.postal_code
                        lookupMessage =
                            "Check the suggested address and add your house or flat number."
                    }
                }
            },
            cancel = { showMap = false }
        )
        return
    }
    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        SectionTitle(if (initial.id == null) "Add an address" else "Edit address")
        if (BuildConfig.MAPS_ENABLED) {
            OutlinedButton(onClick = { showMap = true }, enabled = !busy) {
                Text(if (latitude == null) "Choose location on map" else "Move saved pin")
            }
            if (latitude != null) Text("Delivery pin selected")
        }
        lookupMessage?.let { Text(it) }
        ShopField("Recipient name", name, { name = it })
        ShopField("Phone", phone, {
            phone = it
        }, keyboard = KeyboardOptions(keyboardType = KeyboardType.Phone))
        ShopField("House / flat number and street", line1, {
            line1 =
                it
        })
        ShopField("Landmark (optional)", landmark, {
            landmark =
                it
        })
        if (locality.isNotBlank()) Text("Area: $locality")
        ShopField("City / town", city, {
            city =
                it
        })
        ShopField("State", region, { region = it })
        TextButton(onClick = { moreDetails = !moreDetails }) {
            Text(if (moreDetails) "Fewer details" else "More address details")
        }
        if (moreDetails) {
            ShopField("Address line 2 (optional)", line2, { line2 = it })
            ShopField("Locality (optional)", locality, { locality = it })
            ShopField("Postal code (optional)", postal, { postal = it })
        }
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
                    city = city, state = region, postal_code = postal.ifBlank { null },
                    latitude = latitude, longitude = longitude
                )
            )
        }
        TextButton(onClick = cancel) { Text("Cancel") }
    }
}
