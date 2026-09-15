package com.goodgrocer.app.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.ShoppingBasket
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Shapes
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.Typography
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.SubcomposeAsyncImage
import com.goodgrocer.app.BuildConfig
import com.goodgrocer.app.data.Product
import com.goodgrocer.app.data.Variant
import java.math.BigDecimal
import java.text.NumberFormat
import java.util.Locale

object Space {
    val small = 8.dp
    val medium = 16.dp
    val large = 24.dp
}
val Forest = Color(0xFF12543D)
val Lime = Color(0xFFD7F28D)
private val Palette = lightColorScheme(
    primary = Forest,
    onPrimary = Color.White,
    primaryContainer = Lime,
    onPrimaryContainer = Color(0xFF163F2B),
    secondary = Color(0xFF6B622F),
    secondaryContainer = Lime,
    onSecondaryContainer = Forest,
    background = Color(0xFFF7F9F5),
    surface = Color.White,
    surfaceContainer = Color(0xFFEDF3EB),
    surfaceTint = Forest,
    surfaceVariant = Color(0xFFEBF0E8),
    onSurface = Color(0xFF203B2D),
    onSurfaceVariant = Color(0xFF657166),
    outlineVariant = Color(0xFFDDE5DA)
)

@Composable
fun GoodgrocerTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = Palette,
        shapes = Shapes(
            small = RoundedCornerShape(10.dp),
            medium = RoundedCornerShape(18.dp),
            large = RoundedCornerShape(26.dp)
        ),
        typography = Typography(
            headlineLarge = androidx.compose.ui.text.TextStyle(
                fontFamily = FontFamily.Serif,
                fontSize = 34.sp,
                lineHeight = 39.sp,
                fontWeight = FontWeight.Bold
            ),
            titleLarge = androidx.compose.ui.text.TextStyle(
                fontSize = 22.sp,
                lineHeight = 28.sp,
                fontWeight = FontWeight.Bold
            ),
            titleMedium = androidx.compose.ui.text.TextStyle(
                fontSize = 17.sp,
                lineHeight = 23.sp,
                fontWeight = FontWeight.SemiBold
            )
        ),
        content = content
    )
}
fun rupees(value: String): String =
    NumberFormat.getCurrencyInstance(Locale.forLanguageTag("en-IN")).format(
        value.toBigDecimalOrNull() ?: BigDecimal.ZERO
    )
fun imageUrl(path: String?): String? = path?.let {
    if (it.startsWith("/")) {
        BuildConfig.API_URL.trimEnd('/') +
            it
    } else {
        it
    }
}

@Composable
fun ProductImage(path: String?, modifier: Modifier = Modifier) {
    SubcomposeAsyncImage(
        model = imageUrl(
            path
        ),
        contentDescription = null,
        contentScale = ContentScale.Fit,
        modifier = modifier.clip(
            RoundedCornerShape(14.dp)
        ).background(MaterialTheme.colorScheme.surfaceVariant),
        loading = {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator(Modifier.size(24.dp), strokeWidth = 2.dp)
            }
        },
        error = {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Icon(
                    Icons.Outlined.ShoppingBasket,
                    null,
                    Modifier.size(40.dp),
                    tint = Forest.copy(alpha = .4f)
                )
            }
        }
    )
}

@Composable
fun Price(variant: Variant) {
    Row(
        horizontalArrangement = Arrangement.spacedBy(6.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(rupees(variant.selling_price), fontWeight = FontWeight.Bold)
        if (variant.selling_price.toBigDecimal() <
            variant.mrp.toBigDecimal()
        ) {
            Text(
                rupees(variant.mrp),
                style = MaterialTheme.typography.labelSmall,
                textDecoration = TextDecoration.LineThrough,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@Composable
fun Quantity(value: Int, change: (Int) -> Unit, enabled: Boolean = true) {
    if (value ==
        0
    ) {
        OutlinedButton(
            onClick = {
                change(1)
            },
            enabled = enabled,
            shape = RoundedCornerShape(
                10.dp
            ),
            contentPadding = PaddingValues(horizontal = 18.dp)
        ) {
            Text("ADD +", fontWeight = FontWeight.Bold)
        }
    } else {
        Surface(
            color = MaterialTheme.colorScheme.primaryContainer,
            shape = RoundedCornerShape(10.dp)
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                TextButton(onClick = {
                    change(
                        value - 1
                    )
                }, modifier = Modifier.size(48.dp)) { Text("−", fontSize = 20.sp) }
                Text("$value", fontWeight = FontWeight.Bold)
                TextButton(onClick = {
                    change(
                        value + 1
                    )
                }, enabled = value < 99 && enabled, modifier = Modifier.size(48.dp)) {
                    Text("+", fontSize = 20.sp)
                }
            }
        }
    }
}

@Composable
fun ProductCard(product: Product, quantity: Int, open: () -> Unit, add: (Variant, Int) -> Unit) {
    val variant = product.variants.firstOrNull { it.available } ?: product.variants.firstOrNull()
    Card(
        onClick = open,
        colors = CardDefaults.cardColors(containerColor = Color.White),
        shape = RoundedCornerShape(18.dp)
    ) {
        Column(
            Modifier.padding(12.dp).fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            ProductImage(product.image_url, Modifier.fillMaxWidth().height(124.dp))
            Text(
                product.brand.name.uppercase(),
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                maxLines = 1
            )
            Text(
                product.name,
                style = MaterialTheme.typography.titleMedium,
                minLines = 2,
                maxLines = 2
            )
            Text(
                variant?.name ?: "No variants",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            if (variant !=
                null
            ) {
                Price(variant)
                if (product.available &&
                    variant.available
                ) {
                    if (product.variants.size >
                        1
                    ) {
                        OutlinedButton(onClick = open, shape = RoundedCornerShape(10.dp)) {
                            Text("Choose size")
                        }
                    } else {
                        Quantity(quantity, { add(variant, it) })
                    }
                } else {
                    Text(
                        "Currently unavailable",
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.error
                    )
                }
            }
        }
    }
}

@Composable
fun EmptyState(
    title: String,
    message: String,
    action: String? = null,
    onAction: () -> Unit = {
    }
) {
    Column(
        Modifier.fillMaxWidth().padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Icon(Icons.Outlined.ShoppingBasket, null, Modifier.size(52.dp), tint = Forest)
        Text(title, style = MaterialTheme.typography.titleLarge)
        Text(message, color = MaterialTheme.colorScheme.onSurfaceVariant)
        if (action !=
            null
        ) {
            Button(onClick = onAction) { Text(action) }
        }
    }
}

@Composable
fun LoadingState() {
    Column(
        Modifier.fillMaxWidth().padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        repeat(3) {
            Box(
                Modifier.fillMaxWidth().height(
                    100.dp
                ).clip(
                    RoundedCornerShape(18.dp)
                ).background(MaterialTheme.colorScheme.surfaceVariant)
            )
        }
        LinearProgressIndicator(Modifier.fillMaxWidth())
    }
}

@Composable
fun SectionTitle(title: String, detail: String? = null) {
    Column(Modifier.padding(vertical = 8.dp)) {
        Text(title, style = MaterialTheme.typography.titleLarge)
        if (detail !=
            null
        ) {
            Text(
                detail,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@Composable
fun PrimaryButton(text: String, enabled: Boolean = true, click: () -> Unit) {
    Button(
        onClick = click,
        enabled = enabled,
        modifier = Modifier.fillMaxWidth().heightIn(min = 52.dp),
        shape = RoundedCornerShape(14.dp)
    ) {
        Text(text, fontWeight = FontWeight.Bold)
    }
}

@Composable
fun ShopField(
    label: String,
    value: String,
    change: (String) -> Unit,
    modifier: Modifier = Modifier,
    keyboard: KeyboardOptions = KeyboardOptions.Default
) {
    OutlinedTextField(
        value = value,
        onValueChange = change,
        label = {
            Text(label)
        },
        modifier = modifier.fillMaxWidth(),
        singleLine = true,
        shape = RoundedCornerShape(
            12.dp
        ),
        keyboardOptions = keyboard
    )
}
