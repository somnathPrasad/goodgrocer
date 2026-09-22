package com.goodgrocer.app.ui

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.LocationOn
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import com.google.android.gms.maps.CameraUpdateFactory
import com.google.android.gms.maps.GoogleMap
import com.google.android.gms.maps.MapView
import com.google.android.gms.maps.model.LatLng
import com.google.android.gms.tasks.CancellationTokenSource

@Composable
fun MapPinPicker(initial: LatLng, confirm: (LatLng) -> Unit, cancel: () -> Unit) {
    val context = LocalContext.current
    val lifecycle = LocalLifecycleOwner.current.lifecycle
    val mapView = remember { MapView(context) }
    var selected by remember { mutableStateOf(initial) }
    var mapState by remember { mutableStateOf<GoogleMap?>(null) }
    var locationMessage by remember { mutableStateOf<String?>(null) }
    fun centerOnCurrentLocation() {
        val currentMap = mapState ?: return
        try {
            LocationServices.getFusedLocationProviderClient(context)
                .getCurrentLocation(
                    Priority.PRIORITY_HIGH_ACCURACY,
                    CancellationTokenSource().token
                )
                .addOnSuccessListener { location ->
                    if (location == null) {
                        locationMessage = "Current location unavailable. Move the map manually."
                    } else {
                        currentMap.animateCamera(
                            CameraUpdateFactory.newLatLngZoom(
                                LatLng(location.latitude, location.longitude),
                                17f
                            )
                        )
                        locationMessage = null
                    }
                }.addOnFailureListener {
                    locationMessage = "Current location unavailable. Move the map manually."
                }
        } catch (_: SecurityException) {
            locationMessage = "Location permission is needed to find your position."
        }
    }
    val locationPermission = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { grants ->
        if (grants.values.any { it }) {
            centerOnCurrentLocation()
        } else {
            locationMessage = "Move the map manually to choose your location."
        }
    }
    DisposableEffect(mapView, lifecycle) {
        mapView.onCreate(null)
        val observer = LifecycleEventObserver { _, event ->
            when (event) {
                Lifecycle.Event.ON_START -> mapView.onStart()
                Lifecycle.Event.ON_RESUME -> mapView.onResume()
                Lifecycle.Event.ON_PAUSE -> mapView.onPause()
                Lifecycle.Event.ON_STOP -> mapView.onStop()
                else -> Unit
            }
        }
        lifecycle.addObserver(observer)
        if (lifecycle.currentState.isAtLeast(Lifecycle.State.STARTED)) mapView.onStart()
        if (lifecycle.currentState.isAtLeast(Lifecycle.State.RESUMED)) mapView.onResume()
        mapView.getMapAsync { map ->
            mapState = map
            map.moveCamera(CameraUpdateFactory.newLatLngZoom(initial, 16f))
            map.setOnCameraIdleListener { selected = map.cameraPosition.target }
        }
        onDispose {
            lifecycle.removeObserver(observer)
            mapView.onPause()
            mapView.onStop()
            mapView.onDestroy()
        }
    }
    Column(Modifier.fillMaxSize(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text("Move the map until the pin is at your delivery entrance.", Modifier.padding(20.dp))
        TextButton(onClick = {
            if (context.checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) ==
                PackageManager.PERMISSION_GRANTED ||
                context.checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) ==
                PackageManager.PERMISSION_GRANTED
            ) {
                centerOnCurrentLocation()
            } else {
                locationPermission.launch(
                    arrayOf(
                        Manifest.permission.ACCESS_COARSE_LOCATION,
                        Manifest.permission.ACCESS_FINE_LOCATION
                    )
                )
            }
        }) { Text("Use my current location") }
        locationMessage?.let { Text(it, Modifier.padding(horizontal = 20.dp)) }
        Box(Modifier.weight(1f).fillMaxWidth()) {
            AndroidView(factory = { mapView }, modifier = Modifier.fillMaxSize())
            Surface(
                modifier = Modifier.align(Alignment.Center).offset(y = (-20).dp),
                shape = androidx.compose.foundation.shape.CircleShape,
                color = Color.White,
                shadowElevation = 8.dp
            ) {
                Icon(
                    Icons.Default.LocationOn,
                    contentDescription = "Selected delivery location",
                    tint = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.padding(8.dp).size(36.dp)
                )
            }
        }
        PrimaryButton("Confirm pin", click = { confirm(selected) })
        TextButton(onClick = cancel, modifier = Modifier.align(Alignment.CenterHorizontally)) {
            Text("Enter address manually")
        }
    }
}
