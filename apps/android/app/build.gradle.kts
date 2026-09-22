import java.util.Properties

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.plugin.compose")
}
val localProperties = Properties().apply {
    rootProject.file("local.properties").takeIf { it.isFile }?.inputStream()?.use { load(it) }
}
android {
    namespace = "com.goodgrocer.app"
    compileSdk = 36
    defaultConfig {
        applicationId = "com.goodgrocer.app"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "1.0.0"
        buildConfigField(
            "String",
            "API_URL",
            "\"${providers.gradleProperty("API_URL").getOrElse("http://10.0.2.2:8000/")}\""
        )
        buildConfigField(
            "String",
            "GOOGLE_WEB_CLIENT_ID",
            "\"${providers.gradleProperty("GOOGLE_WEB_CLIENT_ID").getOrElse("")}\""
        )
        val mapsKey = providers.gradleProperty("GOOGLE_MAPS_API_KEY")
            .getOrElse(localProperties.getProperty("GOOGLE_MAPS_API_KEY", ""))
        manifestPlaceholders["googleMapsApiKey"] = mapsKey
        buildConfigField("boolean", "MAPS_ENABLED", mapsKey.isNotBlank().toString())
        buildConfigField(
            "double",
            "STORE_LATITUDE",
            providers.gradleProperty("STORE_LATITUDE")
                .getOrElse(localProperties.getProperty("STORE_LATITUDE", "20.5937"))
        )
        buildConfigField(
            "double",
            "STORE_LONGITUDE",
            providers.gradleProperty("STORE_LONGITUDE")
                .getOrElse(localProperties.getProperty("STORE_LONGITUDE", "78.9629"))
        )
    }
    buildFeatures {
        compose = true
        buildConfig = true
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    buildTypes { release { isMinifyEnabled = false } }
}
dependencies {
    implementation(platform("androidx.compose:compose-bom:2025.08.01"))
    implementation("androidx.activity:activity-compose:1.10.1")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")
    implementation("androidx.compose.ui:ui-tooling-preview")
    debugImplementation("androidx.compose.ui:ui-tooling")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.9.3")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.9.3")
    implementation("androidx.navigation:navigation-compose:2.9.3")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.10.2")
    implementation("com.squareup.retrofit2:retrofit:3.0.0")
    implementation("com.squareup.retrofit2:converter-moshi:3.0.0")
    implementation("com.squareup.moshi:moshi-kotlin:1.15.2")
    implementation("io.coil-kt:coil-compose:2.7.0")
    implementation("androidx.credentials:credentials:1.6.0")
    implementation("androidx.credentials:credentials-play-services-auth:1.6.0")
    implementation("com.google.android.libraries.identity.googleid:googleid:1.2.0")
    implementation("com.google.android.gms:play-services-maps:20.0.0")
    implementation("com.google.android.gms:play-services-location:21.4.0")
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.10.2")
}

// AGP 9 built-in Kotlin does not expose the legacy Kotlin source-set hooks.
// Run the CLI directly so checks cover application/test sources as well as scripts.
val ktlint by configurations.creating
dependencies { ktlint("com.pinterest.ktlint:ktlint-cli:1.5.0") }
for ((name, format) in listOf("ktlintCheck" to false, "ktlintFormat" to true)) {
    tasks.register<JavaExec>(name) {
        group = "verification"
        classpath = ktlint
        mainClass.set("com.pinterest.ktlint.Main")
        workingDir = rootProject.projectDir
        if (format) args("--format")
        args("**/*.kt", "**/*.kts", "!**/build/**", "!**/.gradle/**")
    }
}
