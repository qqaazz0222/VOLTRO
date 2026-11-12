plugins {
    alias(libs.plugins.android.application)
}

android {
    namespace = "com.qqaazz0222.voltro"
    compileSdk {
        version = release(37)
    }

    defaultConfig {
        applicationId = "com.qqaazz0222.voltro"
        minSdk = 28
        targetSdk = 37
        versionCode = 2
        versionName = "1.0.0-mvp"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        release {
            optimization {
                enable = true
            }
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
    sourceSets.getByName("main").assets.srcDir("../../mock-data")
    sourceSets.getByName("main").assets.srcDir("../../licenses")
}

dependencies {
    implementation("ai.pleos.playground:Vehicle:2.3.2")
    implementation("androidx.activity:activity-ktx:1.12.1")
    implementation("androidx.lifecycle:lifecycle-viewmodel-ktx:2.10.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.10.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.9.0")
    implementation(libs.androidx.appcompat)
    implementation(libs.androidx.core.ktx)
    implementation(libs.material)
    testImplementation(libs.junit)
    androidTestImplementation(libs.androidx.espresso.core)
    androidTestImplementation(libs.androidx.junit)
}
