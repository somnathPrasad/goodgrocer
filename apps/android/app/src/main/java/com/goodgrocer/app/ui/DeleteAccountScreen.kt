package com.goodgrocer.app.ui

import android.app.Activity
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.credentials.exceptions.GetCredentialCancellationException
import androidx.credentials.exceptions.GetCredentialException
import com.goodgrocer.app.BuildConfig
import com.google.android.libraries.identity.googleid.GoogleIdTokenParsingException
import kotlinx.coroutines.launch

@Composable
fun DeleteAccountScreen(vm: ShopViewModel, cancel: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val state = collectShopState(vm)
    var token by remember { mutableStateOf<String?>(null) }
    var selectedEmail by remember { mutableStateOf<String?>(null) }
    var pickingAccount by remember { mutableStateOf(false) }
    var authenticationError by remember { mutableStateOf<String?>(null) }

    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(18.dp)
    ) {
        SectionTitle(
            "Delete your Goodgrocer account",
            "This permanently removes your Goodgrocer identity and reusable personal data."
        )
        Card(
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.errorContainer
            ),
            shape = RoundedCornerShape(18.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(
                Modifier.padding(18.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                Text("What will happen", fontWeight = FontWeight.Bold)
                Text("• Saved addresses, favourites and account sessions will be deleted.")
                Text("• Your basket and other customer data on this device will be cleared.")
                Text("• Active orders will continue, but you will lose access to tracking.")
                Text("• Signing in later creates a new account without restoring history.")
            }
        }
        if (token == null) {
            Text(
                "Choose the Google account currently used with Goodgrocer. " +
                    "Selecting another account will not delete anything."
            )
            OutlinedButton(
                onClick = {
                    authenticationError = null
                    if (BuildConfig.GOOGLE_WEB_CLIENT_ID.isBlank()) {
                        authenticationError = "Google authentication is not configured."
                    } else {
                        pickingAccount = true
                        scope.launch {
                            try {
                                val credential = pickGoogleAccount(
                                    context as Activity,
                                    BuildConfig.GOOGLE_WEB_CLIENT_ID
                                )
                                token = credential.idToken
                                selectedEmail = credential.id
                            } catch (_: GetCredentialCancellationException) {
                                // Stay on the explanation when account selection is dismissed.
                            } catch (_: GetCredentialException) {
                                authenticationError =
                                    "Google authentication could not start. Please try again."
                            } catch (_: GoogleIdTokenParsingException) {
                                authenticationError =
                                    "Google returned an unreadable account. Please try again."
                            } catch (_: IllegalStateException) {
                                authenticationError = "Choose a Google account to continue."
                            } finally {
                                pickingAccount = false
                            }
                        }
                    }
                },
                enabled = !pickingAccount && !state.actionLoading,
                modifier = Modifier.fillMaxWidth()
            ) {
                if (pickingAccount) {
                    CircularProgressIndicator(strokeWidth = 2.dp)
                } else {
                    Text("Continue with Google")
                }
            }
        } else {
            Text("Selected Google account", style = MaterialTheme.typography.labelLarge)
            Text(selectedEmail.orEmpty(), style = MaterialTheme.typography.titleMedium)
            Text(
                "Deletion is permanent. Active orders will continue using their retained " +
                    "delivery details until completion or the 30-day limit."
            )
            Button(
                onClick = {
                    val selectedToken = token ?: return@Button
                    token = null
                    selectedEmail = null
                    vm.deleteAccount(selectedToken)
                },
                enabled = !state.actionLoading,
                colors = ButtonDefaults.buttonColors(
                    containerColor = MaterialTheme.colorScheme.error,
                    contentColor = MaterialTheme.colorScheme.onError
                ),
                modifier = Modifier.fillMaxWidth()
            ) {
                if (state.actionLoading) {
                    CircularProgressIndicator(strokeWidth = 2.dp)
                } else {
                    Text("Delete Goodgrocer account")
                }
            }
            OutlinedButton(
                onClick = {
                    token = null
                    selectedEmail = null
                },
                modifier = Modifier.fillMaxWidth()
            ) { Text("Choose a different account") }
        }
        authenticationError?.let {
            Text(it, color = MaterialTheme.colorScheme.error)
        }
        state.error?.let {
            Text(it, color = MaterialTheme.colorScheme.error)
        }
        OutlinedButton(onClick = cancel, modifier = Modifier.fillMaxWidth()) {
            Text("Cancel")
        }
    }
}
