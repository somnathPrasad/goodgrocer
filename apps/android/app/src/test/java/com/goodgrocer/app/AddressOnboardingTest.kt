package com.goodgrocer.app

import com.goodgrocer.app.data.AddressOnboarding
import com.goodgrocer.app.data.Api
import com.goodgrocer.app.data.offerAddressOnboarding
import java.io.IOException
import java.lang.reflect.Proxy
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class AddressOnboardingTest {
    private fun api(call: (String) -> AddressOnboarding): Api = Proxy.newProxyInstance(
        Api::class.java.classLoader,
        arrayOf(Api::class.java)
    ) { _, method, _ -> call(method.name) } as Api

    @Test
    fun unavailableEligibilityDoesNotConsumeTheOffer() = runTest {
        val calls = mutableListOf<String>()
        val api = api {
            calls.add(it)
            throw IOException("Offline")
        }
        assertFalse(api.offerAddressOnboarding())
        assertEquals(listOf("addressOnboarding"), calls)
    }

    @Test
    fun ineligibleCustomerDoesNotRequestAClaim() = runTest {
        val calls = mutableListOf<String>()
        val api = api {
            calls.add(it)
            AddressOnboarding(false)
        }
        assertFalse(api.offerAddressOnboarding())
        assertEquals(listOf("addressOnboarding"), calls)
    }

    @Test
    fun onlyTheDeviceGrantedTheOfferShowsIt() = runTest {
        val api = api { AddressOnboarding(it == "addressOnboarding") }
        assertFalse(api.offerAddressOnboarding())
        assertTrue(api { AddressOnboarding(true) }.offerAddressOnboarding())
    }

    @Test
    fun unavailableClaimAllowsBrowsing() = runTest {
        val api = api {
            if (it == "claimAddressOnboarding") throw IOException("Offline")
            AddressOnboarding(true)
        }
        assertFalse(api.offerAddressOnboarding())
    }

    @Test
    fun leavingTheEntryFlowCancelsTheCheck() = runTest {
        val api = api { throw CancellationException("Signed out") }
        try {
            api.offerAddressOnboarding()
            throw AssertionError("Cancellation must propagate")
        } catch (_: CancellationException) {
            // Never navigate from a cancelled startup check.
        }
    }
}
