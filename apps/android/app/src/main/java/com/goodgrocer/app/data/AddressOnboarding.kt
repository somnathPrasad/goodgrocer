package com.goodgrocer.app.data

import kotlinx.coroutines.CancellationException

/** A failed eligibility read leaves the offer untouched; browsing can continue. */
suspend fun Api.offerAddressOnboarding(): Boolean = try {
    addressOnboarding().eligible && claimAddressOnboarding().eligible
} catch (error: CancellationException) {
    throw error
} catch (_: Exception) {
    false
}
