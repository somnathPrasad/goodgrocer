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

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ShopApp(vm: ShopViewModel) {
    val state by vm.state.collectAsStateWithLifecycle()
    val cart by vm.cart.collectAsStateWithLifecycle()
    val signedIn by vm.signedIn.collectAsStateWithLifecycle()
    val nav = rememberNavController()
    val entry by nav.currentBackStackEntryAsState()
    val route = entry?.destination?.route ?: "home"
    val snackbar = remember { SnackbarHostState() }
    LaunchedEffect(state.error, state.message) {
        (state.error ?: state.message)?.let {
            snackbar.showSnackbar(it, duration = SnackbarDuration.Long)
            vm.clearMessage()
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
        navigate(if (signedIn) destination else "login?next=$destination")
    }
    Scaffold(snackbarHost = { SnackbarHost(snackbar) }, topBar = {
        if (route !=
            "home"
        ) {
            TopAppBar(title = {
                Text(
                    when {
                        route.startsWith("product") -> "From your store"
                        route.startsWith("category") -> "Shop by aisle"
                        route.startsWith("login") -> "Sign in"
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
                !route.startsWith("login")
            ) {
                Surface(color = Forest, onClick = {
                    navigate("cart")
                }) {
                    Row(
                        Modifier.fillMaxWidth().padding(Space.medium),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(
                            "${cart.sumOf {
                                it.quantity
                            }} items · ${rupees(cartSubtotal(cart).toPlainString())}",
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
            startDestination = "home",
            modifier = Modifier.padding(padding)
        ) {
            composable("home") {
                CatalogueScreen(vm, state, cart, home = true, open = {
                    navigate("product/$it")
                }, search = { navigate("search") }, category = { navigate("category/$it") })
            }
            composable("search") {
                CatalogueScreen(vm, state, cart, open = { navigate("product/$it") })
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
                    state,
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
                ProductScreen(page.arguments!!.getInt("id"), vm, state, cart, signedIn, {
                    authenticated("favourites")
                })
            }
            composable("cart") {
                CartScreen(vm, cart, { authenticated("checkout") }, { navigate("home") })
            }
            composable(
                "login?next={next}",
                arguments = listOf(
                    navArgument("next") {
                        defaultValue =
                            "account"
                    }
                )
            ) { page ->
                LoginScreen(vm, state) {
                    val next =
                        page.arguments?.getString("next") ?: "account"
                    nav.popBackStack()
                    navigate(next)
                }
            }
            composable("favourites") {
                if (!signedIn) {
                    SignInPrompt {
                        authenticated("favourites")
                    }
                } else {
                    FavouritesScreen(vm, state, cart) { navigate("product/$it") }
                }
            }
            composable("addresses") {
                if (!signedIn) {
                    SignInPrompt {
                        authenticated("addresses")
                    }
                } else {
                    AddressScreen(vm, state)
                }
            }
            composable("checkout") {
                if (!signedIn) {
                    SignInPrompt { authenticated("checkout") }
                } else {
                    CheckoutScreen(vm, state, cart, { navigate("addresses") }) { id ->
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
                    OrdersScreen(vm, state) { navigate("order/$it") }
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
                    vm,
                    state
                ) {
                    navigate("cart")
                }
            }
            composable("account") {
                AccountScreen(signedIn, {
                    authenticated("account")
                }, { authenticated("addresses") }, { vm.logout() })
            }
        }
    }
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
