package com.goodgrocer.app.ui

import android.app.Activity
import android.graphics.Paint
import android.graphics.Typeface
import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.translate
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.credentials.exceptions.GetCredentialCancellationException
import androidx.credentials.exceptions.GetCredentialException
import com.goodgrocer.app.BuildConfig
import com.google.android.libraries.identity.googleid.GoogleIdTokenParsingException
import kotlinx.coroutines.launch

private val Cream = Color(0xFFF8F6EB)
private val Leaf = Color(0xFF2E7652)
private val Peach = Color(0xFFFFD4A3)
private val Orange = Color(0xFFF4934B)

@Composable
fun EntryScreen(vm: ShopViewModel, done: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val state = collectShopState(vm)
    var pickingAccount by remember { mutableStateOf(false) }
    var signInError by remember { mutableStateOf<String?>(null) }

    Column(
        Modifier.fillMaxSize().background(Cream).padding(horizontal = 28.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Row(
            Modifier.fillMaxWidth().padding(top = 34.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                Modifier.size(38.dp).background(Forest, RoundedCornerShape(12.dp)),
                contentAlignment = Alignment.Center
            ) {
                Text("g", color = Lime, fontSize = 30.sp, fontWeight = FontWeight.Bold)
            }
            Text(
                "goodgrocer",
                Modifier.padding(start = 10.dp),
                color = Forest,
                fontSize = 22.sp,
                fontWeight = FontWeight.Bold
            )
        }

        GroceryArtwork(Modifier.fillMaxWidth().weight(1f))

        Column(
            Modifier.fillMaxWidth().padding(bottom = 34.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            Text(
                "Fresh finds,\nright around the corner.",
                color = Forest,
                style = MaterialTheme.typography.headlineLarge,
                lineHeight = 39.sp
            )
            Text(
                "Your neighbourhood store is ready for your everyday list.",
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                style = MaterialTheme.typography.bodyLarge
            )
            Spacer(Modifier.height(9.dp))
            Button(
                onClick = {
                    signInError = null
                    if (BuildConfig.GOOGLE_WEB_CLIENT_ID.isBlank()) {
                        signInError = "Google sign-in is not configured for this app."
                    } else {
                        pickingAccount = true
                        scope.launch {
                            try {
                                val credential = pickGoogleAccount(
                                    context as Activity,
                                    BuildConfig.GOOGLE_WEB_CLIENT_ID
                                )
                                vm.googleSignIn(credential.idToken, done)
                            } catch (_: GetCredentialCancellationException) {
                                // The entry screen remains available if the sheet is dismissed.
                            } catch (_: GetCredentialException) {
                                signInError = "Google sign-in could not start. Please try again."
                            } catch (_: GoogleIdTokenParsingException) {
                                signInError =
                                    "Google sign-in returned an unreadable account. Please try again."
                            } catch (_: IllegalStateException) {
                                signInError = "Choose a Google account to continue."
                            } finally {
                                pickingAccount = false
                            }
                        }
                    }
                },
                enabled = !pickingAccount && !state.actionLoading,
                modifier = Modifier.fillMaxWidth().height(58.dp),
                shape = RoundedCornerShape(18.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color.White,
                    contentColor = Forest
                )
            ) {
                if (pickingAccount || state.actionLoading) {
                    CircularProgressIndicator(Modifier.size(22.dp), strokeWidth = 2.dp)
                } else {
                    GoogleMark(Modifier.size(22.dp))
                    Text(
                        "Continue with Google",
                        Modifier.padding(start = 12.dp),
                        fontWeight = FontWeight.SemiBold,
                        fontSize = 16.sp
                    )
                }
            }
            signInError?.let {
                Text(
                    it,
                    color = MaterialTheme.colorScheme.error,
                    style = MaterialTheme.typography.bodySmall
                )
            }
            Text(
                "A little closer to everything you need.",
                Modifier.fillMaxWidth(),
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                style = MaterialTheme.typography.bodySmall,
                textAlign = TextAlign.Center
            )
        }
    }
}

@Composable
private fun GoogleMark(modifier: Modifier = Modifier) {
    Canvas(modifier) {
        val stroke = size.minDimension * .22f
        val inset = stroke / 2
        val arcSize = Size(size.width - stroke, size.height - stroke)
        drawArc(
            Color(0xFF4285F4),
            -42f,
            90f,
            false,
            Offset(inset, inset),
            arcSize,
            style = Stroke(stroke)
        )
        drawArc(
            Color(0xFF34A853),
            48f,
            82f,
            false,
            Offset(inset, inset),
            arcSize,
            style = Stroke(stroke)
        )
        drawArc(
            Color(0xFFFBBC05),
            130f,
            70f,
            false,
            Offset(inset, inset),
            arcSize,
            style = Stroke(stroke)
        )
        drawArc(
            Color(0xFFEA4335),
            200f,
            118f,
            false,
            Offset(inset, inset),
            arcSize,
            style = Stroke(stroke)
        )
        drawLine(
            Color(0xFF4285F4),
            Offset(size.width * .54f, size.height * .50f),
            Offset(size.width * .94f, size.height * .50f),
            stroke
        )
    }
}

@Composable
private fun GroceryArtwork(modifier: Modifier = Modifier) {
    val tagPaint = remember {
        Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Forest.toArgb()
            typeface = Typeface.DEFAULT_BOLD
            textAlign = Paint.Align.CENTER
        }
    }
    val produceDrop = remember { Animatable(-16f) }
    LaunchedEffect(Unit) {
        produceDrop.animateTo(0f, tween(850, easing = FastOutSlowInEasing))
    }
    Canvas(modifier) {
        val scale = minOf(size.width / 360f, size.height / 330f)
        fun p(x: Float, y: Float) = Offset(x * scale, y * scale)
        translate(
            left = (size.width - 360f * scale) / 2f,
            top = (size.height - 330f * scale) / 2f
        ) {
            drawCircle(Color(0xFFE8EFCE), 132f * scale, p(180f, 168f))
            drawCircle(
                Color(0xFFDCE9C5),
                105f * scale,
                p(180f, 168f),
                style = Stroke(1.5f * scale)
            )
            drawCircle(Peach, 11f * scale, p(43f, 121f))
            drawCircle(Lime, 8f * scale, p(315f, 91f))
            drawCircle(Orange.copy(alpha = .55f), 6f * scale, p(314f, 255f))
            drawLine(Leaf.copy(alpha = .4f), p(47f, 246f), p(66f, 230f), 3f * scale)
            drawLine(Leaf.copy(alpha = .4f), p(305f, 215f), p(320f, 229f), 3f * scale)
            drawOval(
                Color(0x330B4834),
                topLeft = p(79f, 281f),
                size = Size(205f * scale, 28f * scale)
            )

            translate(top = produceDrop.value * scale) {
                // Bread, with three cuts in its crust.
                val bread = Path().apply {
                    moveTo(78f * scale, 167f * scale)
                    lineTo(87f * scale, 107f * scale)
                    cubicTo(
                        89f * scale,
                        88f * scale,
                        114f * scale,
                        85f * scale,
                        124f * scale,
                        106f * scale
                    )
                    lineTo(141f * scale, 167f * scale)
                    close()
                }
                drawPath(bread, Color(0xFFD7964F))
                drawLine(Color(0xFFFFD799), p(98f, 109f), p(114f, 121f), 5f * scale)
                drawLine(Color(0xFFFFD799), p(94f, 130f), p(121f, 143f), 5f * scale)
                drawLine(Color(0xFFFFD799), p(91f, 151f), p(126f, 162f), 5f * scale)

                // Two broad lettuce leaves with veins.
                val leftLeaf = Path().apply {
                    moveTo(156f * scale, 166f * scale)
                    cubicTo(
                        105f * scale,
                        131f * scale,
                        109f * scale,
                        89f * scale,
                        136f * scale,
                        80f * scale
                    )
                    cubicTo(
                        145f * scale,
                        70f * scale,
                        158f * scale,
                        77f * scale,
                        163f * scale,
                        87f * scale
                    )
                    cubicTo(
                        184f * scale,
                        64f * scale,
                        208f * scale,
                        87f * scale,
                        194f * scale,
                        112f * scale
                    )
                    cubicTo(
                        209f * scale,
                        141f * scale,
                        183f * scale,
                        159f * scale,
                        156f * scale,
                        166f * scale
                    )
                    close()
                }
                drawPath(leftLeaf, Leaf)
                drawLine(Color(0xFFB6D987), p(157f, 153f), p(148f, 94f), 2.5f * scale)
                drawLine(Color(0xFFB6D987), p(152f, 128f), p(129f, 108f), 2f * scale)
                drawLine(Color(0xFFB6D987), p(153f, 117f), p(176f, 93f), 2f * scale)

                // A milk carton makes the assortment read as everyday groceries.
                val carton = Path().apply {
                    moveTo(190f * scale, 113f * scale)
                    lineTo(205f * scale, 91f * scale)
                    lineTo(231f * scale, 91f * scale)
                    lineTo(245f * scale, 113f * scale)
                    lineTo(245f * scale, 169f * scale)
                    lineTo(190f * scale, 169f * scale)
                    close()
                }
                drawPath(carton, Color(0xFFECF5E9))
                drawPath(
                    Path().apply {
                        moveTo(190f * scale, 113f * scale)
                        lineTo(205f * scale, 91f * scale)
                        lineTo(231f * scale, 91f * scale)
                        lineTo(245f * scale, 113f * scale)
                        close()
                    },
                    Color(0xFF78A88B)
                )
                drawRect(Leaf, p(193f, 129f), Size(49f * scale, 25f * scale))
                drawCircle(Color.White, 7f * scale, p(218f, 141f))
                drawLine(Color(0xFFC8E1CD), p(231f, 93f), p(231f, 111f), 2f * scale)

                // Tomatoes and a curved bunch of bananas sit at the front.
                drawCircle(Color(0xFFEA654B), 24f * scale, p(255f, 151f))
                drawCircle(Color(0xFFF47B5A), 15f * scale, p(249f, 146f))
                drawPath(
                    Path().apply {
                        moveTo(254f * scale, 128f * scale)
                        lineTo(246f * scale, 120f * scale)
                        lineTo(257f * scale, 123f * scale)
                        lineTo(263f * scale, 116f * scale)
                        lineTo(264f * scale, 126f * scale)
                        lineTo(273f * scale, 128f * scale)
                        close()
                    },
                    Forest
                )
                val banana = Path().apply {
                    moveTo(138f * scale, 138f * scale)
                    cubicTo(
                        159f * scale,
                        155f * scale,
                        190f * scale,
                        155f * scale,
                        216f * scale,
                        127f * scale
                    )
                    cubicTo(
                        206f * scale,
                        164f * scale,
                        165f * scale,
                        179f * scale,
                        138f * scale,
                        149f * scale
                    )
                    close()
                }
                drawPath(banana, Color(0xFFF6C94E))
                drawLine(Color(0xFFE8AA37), p(138f, 145f), p(132f, 142f), 4f * scale)
                drawLine(Color(0xFFE8AA37), p(216f, 128f), p(220f, 122f), 3f * scale)
            }

            // The straps pass in front of the groceries and tuck under the rim.
            val leftHandle = Path().apply {
                moveTo(103f * scale, 167f * scale)
                cubicTo(
                    103f * scale,
                    104f * scale,
                    164f * scale,
                    85f * scale,
                    169f * scale,
                    166f * scale
                )
            }
            val rightHandle = Path().apply {
                moveTo(192f * scale, 166f * scale)
                cubicTo(
                    200f * scale,
                    94f * scale,
                    263f * scale,
                    103f * scale,
                    259f * scale,
                    167f * scale
                )
            }
            drawPath(leftHandle, Forest, style = Stroke(9f * scale))
            drawPath(rightHandle, Forest, style = Stroke(9f * scale))

            // A broad canvas tote with a folded rim, seams, and a stitched pocket.
            val tote = Path().apply {
                moveTo(75f * scale, 165f * scale)
                lineTo(285f * scale, 165f * scale)
                lineTo(278f * scale, 258f * scale)
                cubicTo(
                    277f * scale,
                    279f * scale,
                    262f * scale,
                    292f * scale,
                    241f * scale,
                    292f * scale
                )
                lineTo(119f * scale, 292f * scale)
                cubicTo(
                    98f * scale,
                    292f * scale,
                    83f * scale,
                    279f * scale,
                    82f * scale,
                    258f * scale
                )
                close()
            }
            drawPath(tote, Color(0xFFE7CB98))
            drawPath(
                Path().apply {
                    moveTo(75f * scale, 165f * scale)
                    lineTo(98f * scale, 165f * scale)
                    lineTo(108f * scale, 285f * scale)
                    cubicTo(
                        92f * scale,
                        281f * scale,
                        83f * scale,
                        271f * scale,
                        82f * scale,
                        258f * scale
                    )
                    close()
                },
                Color(0xFFD6B77F)
            )
            drawRoundRect(
                Forest,
                topLeft = p(75f, 161f),
                size = Size(210f * scale, 15f * scale),
                cornerRadius = CornerRadius(7f * scale)
            )
            drawLine(Color(0xFFB99661), p(111f, 181f), p(119f, 279f), 1.5f * scale)
            drawLine(Color(0xFFF3DCB4), p(264f, 181f), p(257f, 275f), 2f * scale)
            drawRoundRect(
                Color(0xFFEED7AD),
                topLeft = p(129f, 203f),
                size = Size(102f * scale, 66f * scale),
                cornerRadius = CornerRadius(8f * scale)
            )
            drawRoundRect(
                Color(0xFFB99661),
                topLeft = p(129f, 203f),
                size = Size(102f * scale, 66f * scale),
                cornerRadius = CornerRadius(8f * scale),
                style = Stroke(1.5f * scale)
            )
            drawLine(Color(0xFFB99661), p(138f, 213f), p(222f, 213f), 1f * scale)
            drawPath(
                Path().apply {
                    moveTo(180f * scale, 252f * scale)
                    cubicTo(
                        164f * scale,
                        242f * scale,
                        167f * scale,
                        226f * scale,
                        179f * scale,
                        230f * scale
                    )
                    cubicTo(
                        186f * scale,
                        222f * scale,
                        199f * scale,
                        231f * scale,
                        180f * scale,
                        252f * scale
                    )
                    close()
                },
                Leaf
            )
            drawLine(Color(0xFFB99661), p(157f, 280f), p(203f, 280f), 1f * scale)

            // The small handle tag carries the monogram without dominating the bag.
            drawLine(Forest, p(237f, 171f), p(251f, 184f), 2f * scale)
            drawRoundRect(
                Lime,
                topLeft = p(243f, 181f),
                size = Size(27f * scale, 33f * scale),
                cornerRadius = CornerRadius(5f * scale)
            )
            drawCircle(Forest, 2f * scale, p(251f, 186f))
            tagPaint.textSize = 17f * scale
            drawContext.canvas.nativeCanvas.drawText(
                "g",
                256f * scale,
                205f * scale,
                tagPaint
            )
        }
    }
}
