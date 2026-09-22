package com.goodgrocer.app.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.automirrored.outlined.ReceiptLong
import androidx.compose.material.icons.outlined.FavoriteBorder
import androidx.compose.material.icons.outlined.PersonOutline
import androidx.compose.material.icons.outlined.Refresh
import androidx.compose.material.icons.outlined.Search
import androidx.compose.material.icons.outlined.Storefront
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarDuration
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.goodgrocer.app.data.cartSubtotal
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.map

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ShopApp(vm: ShopViewModel) {
    val messageFlow = remember(vm) {
        vm.state.map { it.error ?: it.message }.distinctUntilChanged()
    }
    val message by messageFlow
        .collectAsStateWithLifecycle(null)
    val cart by vm.cart.collectAsStateWithLifecycle()
    val signedIn by vm.signedIn.collectAsStateWithLifecycle()
    val nav = rememberNavController()
    val entry by nav.currentBackStackEntryAsState()
    val startDestination = remember { if (signedIn) "home" else "entry" }
    val route = entry?.destination?.route ?: startDestination
    val snackbar = remember { SnackbarHostState() }
    LaunchedEffect(message) {
        message?.let {
            snackbar.showSnackbar(it, duration = SnackbarDuration.Long)
            vm.clearMessage()
        }
    }
    LaunchedEffect(signedIn, entry?.destination?.route) {
        if (!signedIn && entry != null && route != "entry") {
            nav.navigate("entry") {
                popUpTo(nav.graph.id) { inclusive = true }
                launchSingleTop = true
            }
        }
    }
    val navigate: (String) -> Unit = { destination ->
        nav.navigate(destination) {
            launchSingleTop =
                true
        }
    }
    val authenticated: (
        String
    ) -> Unit = { destination ->
        navigate(if (signedIn) destination else "entry")
    }
    Scaffold(snackbarHost = { SnackbarHost(snackbar) }, topBar = {
        if (route != "home" && route != "entry") {
            TopAppBar(title = {
                Text(
                    when {
                        route.startsWith("product") -> "From your store"
                        route.startsWith("category") -> "Shop by aisle"
                        route.startsWith("order/") -> "Your order"
                        else -> route.replaceFirstChar { it.uppercase() }
                    }
                )
            }, navigationIcon = {
                IconButton(onClick = {
                    nav.popBackStack()
                }) { Icon(Icons.AutoMirrored.Outlined.ArrowBack, "Back") }
            }, actions = {
                if (route ==
                    "orders"
                ) {
                    IconButton(onClick = {
                        vm.loadOrders()
                    }) { Icon(Icons.Outlined.Refresh, "Refresh orders") }
                }
            })
        }
    }, bottomBar = {
        Column {
            if (cart.isNotEmpty() &&
                route !in listOf("cart", "checkout") &&
                route != "entry"
            ) {
                val basketSummary = remember(cart) {
                    val count = cart.sumOf { it.quantity }
                    val total = rupees(cartSubtotal(cart).toPlainString())
                    "$count items · $total"
                }
                Surface(color = Forest, onClick = {
                    navigate("cart")
                }) {
                    Row(
                        Modifier.fillMaxWidth().padding(Space.medium),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(
                            basketSummary,
                            color = MaterialTheme.colorScheme.onPrimary
                        )
                        Text("View basket →", color = MaterialTheme.colorScheme.onPrimary)
                    }
                }
            }
            if (route in
                listOf("home", "search", "favourites", "orders", "account")
            ) {
                NavigationBar {
                    listOf(
                        Triple("home", "Shop", Icons.Outlined.Storefront),
                        Triple("search", "Search", Icons.Outlined.Search),
                        Triple("favourites", "Saved", Icons.Outlined.FavoriteBorder),
                        Triple("orders", "Orders", Icons.AutoMirrored.Outlined.ReceiptLong),
                        Triple("account", "You", Icons.Outlined.PersonOutline)
                    ).forEach { (path, label, icon) ->
                        NavigationBarItem(
                            selected =
                            route == path,
                            onClick = {
                                nav.navigate(path) {
                                    popUpTo("home")
                                    launchSingleTop =
                                        true
                                }
                            },
                            icon = { Icon(icon, label) },
                            label = { Text(label) }
                        )
                    }
                }
            }
        }
    }) { padding ->
        NavHost(
            navController = nav,
            startDestination = startDestination,
            modifier = Modifier.padding(padding)
        ) {
            composable("entry") {
                EntryScreen(vm) {
                    nav.navigate("home") {
                        popUpTo("entry") { inclusive = true }
                        launchSingleTop = true
                    }
                }
            }
            composable("home") {
                CatalogueScreen(vm, cart, home = true, open = {
                    navigate("product/$it")
                }, search = { navigate("search") }, category = { navigate("category/$it") })
            }
            composable("search") {
                CatalogueScreen(
                    vm,
                    cart,
                    open = { navigate("product/$it") },
                    autoFocusSearch = true
                )
            }
            composable(
                "category/{id}",
                arguments = listOf(
                    navArgument("id") {
                        type =
                            NavType.IntType
                    }
                )
            ) { page ->
                CatalogueScreen(
                    vm,
                    cart,
                    categoryId = page.arguments!!.getInt(
                        "id"
                    ),
                    open = {
                        navigate("product/$it")
                    }
                )
            }
            composable(
                "product/{id}",
                arguments = listOf(
                    navArgument("id") {
                        type = NavType.IntType
                    }
                )
            ) { page ->
                ProductScreen(page.arguments!!.getInt("id"), vm, cart, signedIn, {
                    authenticated("favourites")
                })
            }
            composable("cart") {
                CartScreen(vm, cart, { authenticated("checkout") }, { navigate("home") })
            }
            composable("favourites") {
                if (!signedIn) {
                    SignInPrompt {
                        authenticated("favourites")
                    }
                } else {
                    FavouritesScreen(vm, cart) { navigate("product/$it") }
                }
            }
            composable("addresses") {
                if (!signedIn) {
                    SignInPrompt {
                        authenticated("addresses")
                    }
                } else {
                    AddressScreen(vm)
                }
            }
            composable("checkout") {
                if (!signedIn) {
                    SignInPrompt { authenticated("checkout") }
                } else {
                    CheckoutScreen(vm, cart, { navigate("addresses") }) { id ->
                        nav.navigate("order/$id?success=true") {
                            popUpTo("cart") {
                                inclusive =
                                    true
                            }
                        }
                    }
                }
            }
            composable("orders") {
                if (!signedIn) {
                    SignInPrompt {
                        authenticated("orders")
                    }
                } else {
                    OrdersScreen(vm) { navigate("order/$it") }
                }
            }
            composable(
                "order/{id}?success={success}",
                arguments = listOf(
                    navArgument("id") {
                        type =
                            NavType.IntType
                    },
                    navArgument("success") {
                        type = NavType.BoolType
                        defaultValue =
                            false
                    }
                )
            ) { page ->
                OrderScreen(
                    page.arguments!!.getInt("id"),
                    page.arguments!!.getBoolean("success"),
                    vm
                ) {
                    navigate("cart")
                }
            }
            composable("account") {
                AccountScreen(
                    signedIn = signedIn,
                    login = { authenticated("account") },
                    onAddresses = { authenticated("addresses") },
                    onOrders = { authenticated("orders") },
                    onFavourites = { authenticated("favourites") },
                    logout = { vm.logout() }
                )
            }
        }
    }
}

@Composable
fun collectShopState(vm: ShopViewModel): ShopState {
    val state by vm.state.collectAsStateWithLifecycle()
    return state
}

@Composable
fun SignInPrompt(login: () -> Unit) {
    EmptyState(
        "Your store, saved",
        "Sign in to access your favourites, addresses and orders. Your basket stays on this device.",
        "Sign in",
        login
    )
}
