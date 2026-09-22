package com.goodgrocer.app.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.KeyboardArrowRight
import androidx.compose.material.icons.automirrored.outlined.Logout
import androidx.compose.material.icons.automirrored.outlined.ReceiptLong
import androidx.compose.material.icons.outlined.FavoriteBorder
import androidx.compose.material.icons.outlined.LocationOn
import androidx.compose.material.icons.outlined.Person
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.goodgrocer.app.BuildConfig
import com.goodgrocer.app.data.Address
import com.goodgrocer.app.data.AddressSuggestion
import com.google.android.gms.maps.model.LatLng

@Composable
fun AccountScreen(
    signedIn: Boolean,
    login: () -> Unit,
    onAddresses: () -> Unit,
    onOrders: () -> Unit,
    onFavourites: () -> Unit,
    logout: () -> Unit
) {
    var showLogoutDialog by remember { mutableStateOf(false) }

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        SectionTitle("Your Account", "Manage your profile, orders, and preferences.")

        if (!signedIn) {
            Card(
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer),
                shape = RoundedCornerShape(20.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(
                    Modifier.padding(20.dp),
                    verticalArrangement = Arrangement.spacedBy(14.dp)
                ) {
                    Row(
                        horizontalArrangement = Arrangement.spacedBy(14.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Surface(
                            color = MaterialTheme.colorScheme.primary,
                            shape = RoundedCornerShape(14.dp),
                            modifier = Modifier.size(48.dp)
                        ) {
                            Box(contentAlignment = Alignment.Center) {
                                Icon(
                                    Icons.Outlined.Person,
                                    contentDescription = null,
                                    tint = MaterialTheme.colorScheme.onPrimary
                                )
                            }
                        }
                        Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                            Text("Welcome to Goodgrocer", style = MaterialTheme.typography.titleMedium)
                            Text("Sign in with Google for full access", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onPrimaryContainer)
                        }
                    }
                    Text(
                        "Sign in to sync your delivery addresses across devices, track live order history, and access your saved grocery wishlist.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onPrimaryContainer
                    )
                    PrimaryButton("Sign in with Google", click = login)
                }
            }
        } else {
            Card(
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                shape = RoundedCornerShape(20.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(
                    Modifier.padding(20.dp),
                    verticalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    Row(
                        horizontalArrangement = Arrangement.spacedBy(14.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Surface(
                            color = MaterialTheme.colorScheme.primaryContainer,
                            shape = RoundedCornerShape(16.dp),
                            modifier = Modifier.size(56.dp)
                        ) {
                            Box(contentAlignment = Alignment.Center) {
                                Text("GG", style = MaterialTheme.typography.titleLarge, color = MaterialTheme.colorScheme.onPrimaryContainer, fontWeight = FontWeight.Bold)
                            }
                        }
                        Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                            Text("Goodgrocer Member", style = MaterialTheme.typography.titleLarge)
                            Row(horizontalArrangement = Arrangement.spacedBy(6.dp), verticalAlignment = Alignment.CenterVertically) {
                                Surface(
                                    color = MaterialTheme.colorScheme.primaryContainer,
                                    shape = RoundedCornerShape(6.dp)
                                ) {
                                    Text(" Verified ", style = MaterialTheme.typography.labelSmall, modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp), color = MaterialTheme.colorScheme.onPrimaryContainer)
                                }
                                Text("Active shopper", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                        }
                    }

                    Row(
                        Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(10.dp)
                    ) {
                        AccountQuickCard(
                            icon = Icons.AutoMirrored.Outlined.ReceiptLong,
                            title = "Orders",
                            subtitle = "History",
                            modifier = Modifier.weight(1f),
                            onClick = onOrders
                        )
                        AccountQuickCard(
                            icon = Icons.Outlined.FavoriteBorder,
                            title = "Saved",
                            subtitle = "Wishlist",
                            modifier = Modifier.weight(1f),
                            onClick = onFavourites
                        )
                        AccountQuickCard(
                            icon = Icons.Outlined.LocationOn,
                            title = "Addresses",
                            subtitle = "Locations",
                            modifier = Modifier.weight(1f),
                            onClick = onAddresses
                        )
                    }
                }
            }
        }

        Text("Shopping & Account", style = MaterialTheme.typography.titleMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)

        if (signedIn) {
            AccountMenuItem(
                icon = Icons.AutoMirrored.Outlined.ReceiptLong,
                title = "Order History",
                subtitle = "Track active deliveries and view past orders",
                onClick = onOrders
            )
            AccountMenuItem(
                icon = Icons.Outlined.LocationOn,
                title = "Delivery Addresses",
                subtitle = "Manage saved home and work locations",
                onClick = onAddresses
            )
            AccountMenuItem(
                icon = Icons.Outlined.FavoriteBorder,
                title = "Saved Favourites",
                subtitle = "View and reorder your favorite items",
                onClick = onFavourites
            )
        } else {
            AccountMenuItem(
                icon = Icons.Outlined.LocationOn,
                title = "Delivery Addresses",
                subtitle = "Sign in to manage saved addresses",
                onClick = login
            )
            AccountMenuItem(
                icon = Icons.AutoMirrored.Outlined.ReceiptLong,
                title = "Order History",
                subtitle = "Sign in to view your order history",
                onClick = login
            )
        }

        if (signedIn) {
            Spacer(Modifier.height(8.dp))
            OutlinedButton(
                onClick = { showLogoutDialog = true },
                modifier = Modifier.fillMaxWidth().heightIn(min = 52.dp),
                shape = RoundedCornerShape(14.dp)
            ) {
                Icon(Icons.AutoMirrored.Outlined.Logout, contentDescription = null, modifier = Modifier.size(18.dp))
                Spacer(Modifier.width(8.dp))
                Text("Sign out of Goodgrocer", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.error)
            }
        }

        Spacer(Modifier.height(16.dp))
    }

    if (showLogoutDialog) {
        AlertDialog(
            onDismissRequest = { showLogoutDialog = false },
            title = { Text("Sign out?") },
            text = { Text("You will need to sign in again with Google to access your synced addresses and order history.") },
            confirmButton = {
                TextButton(onClick = {
                    showLogoutDialog = false
                    logout()
                }) {
                    Text("Sign out", color = MaterialTheme.colorScheme.error)
                }
            },
            dismissButton = {
                TextButton(onClick = { showLogoutDialog = false }) {
                    Text("Cancel")
                }
            }
        )
    }
}

@Composable
fun AccountQuickCard(
    icon: ImageVector,
    title: String,
    subtitle: String,
    modifier: Modifier = Modifier,
    onClick: () -> Unit
) {
    Card(
        onClick = onClick,
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
        shape = RoundedCornerShape(14.dp),
        modifier = modifier
    ) {
        Column(
            Modifier.padding(12.dp).fillMaxWidth(),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            Icon(
                icon,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.primary,
                modifier = Modifier.size(24.dp)
            )
            Text(title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
            Text(subtitle, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@Composable
fun AccountMenuItem(
    icon: ImageVector,
    title: String,
    subtitle: String,
    onClick: () -> Unit
) {
    Card(
        onClick = onClick,
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        shape = RoundedCornerShape(16.dp),
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            Modifier.fillMaxWidth().padding(16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(
                horizontalArrangement = Arrangement.spacedBy(16.dp),
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.weight(1f)
            ) {
                Surface(
                    color = MaterialTheme.colorScheme.surfaceVariant,
                    shape = RoundedCornerShape(12.dp),
                    modifier = Modifier.size(44.dp)
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Icon(icon, contentDescription = null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(22.dp))
                    }
                }
                Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                    Text(title, style = MaterialTheme.typography.titleMedium)
                    Text(subtitle, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
            Icon(
                imageVector = Icons.AutoMirrored.Outlined.KeyboardArrowRight,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onSurfaceVariant
            )
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
