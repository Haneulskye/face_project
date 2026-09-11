package com.faceproject.android.navigation

import android.widget.Toast
import androidx.compose.runtime.Composable
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.faceproject.android.data.CapturedImageHolder
import com.faceproject.android.ui.components.AppScaffold
import com.faceproject.android.ui.screens.history.HistoryScreen
import com.faceproject.android.ui.screens.history.HistoryViewModel
import com.faceproject.android.ui.screens.main.MainScreen
import com.faceproject.android.ui.screens.profile.ProfileScreen
import com.faceproject.android.ui.screens.profile.ProfileViewModel
import com.faceproject.android.ui.screens.register.RegisterScreen
import com.faceproject.android.ui.screens.register.RegisterSuccessScreen
import com.faceproject.android.ui.screens.register.RegisterViewModel
import com.faceproject.android.ui.screens.scan.FaceScanScreen
import com.faceproject.android.ui.screens.scan.FaceScanViewModel

@Composable
fun FaceAuthNavGraph(navController: NavHostController = rememberNavController()) {
    val context = LocalContext.current
    // Activity-scoped: shared between the scan screen (captures the photo)
    // and the registration screen (uploads it), regardless of back-stack churn.
    val capturedImageHolder: CapturedImageHolder = viewModel()

    fun goHome() {
        navController.navigate(Routes.MAIN) {
            popUpTo(Routes.MAIN) { inclusive = true }
            launchSingleTop = true
        }
    }

    fun showAbout() {
        Toast.makeText(
            context,
            "얼굴·홍채·rPPG 기반 멀티모달 인증 시스템 데모 앱",
            Toast.LENGTH_LONG
        ).show()
    }

    NavHost(navController = navController, startDestination = Routes.MAIN) {

        composable(Routes.MAIN) {
            AppScaffold(title = "메인화면", onNavigateHome = ::goHome, onShowAbout = ::showAbout) { padding ->
                MainScreen(
                    padding = padding,
                    onStartFaceScan = { navController.navigate(Routes.SCAN) }
                )
            }
        }

        composable(Routes.SCAN) {
            val viewModel: FaceScanViewModel = viewModel()
            AppScaffold(title = "얼굴 인식 중", onNavigateHome = ::goHome, onShowAbout = ::showAbout) { padding ->
                FaceScanScreen(
                    padding = padding,
                    viewModel = viewModel,
                    capturedImageHolder = capturedImageHolder,
                    onCapturedForRegistration = { navController.navigate(Routes.REGISTER) },
                    onAuthenticated = { name ->
                        navController.navigate(Routes.profile(name)) {
                            popUpTo(Routes.MAIN)
                        }
                    }
                )
            }
        }

        composable(Routes.REGISTER) {
            val viewModel: RegisterViewModel = viewModel()
            AppScaffold(title = "회원가입", onNavigateHome = ::goHome, onShowAbout = ::showAbout) { padding ->
                RegisterScreen(
                    padding = padding,
                    viewModel = viewModel,
                    capturedImageHolder = capturedImageHolder,
                    onRegistered = { name, nickname ->
                        navController.navigate(Routes.registerSuccess(name, nickname)) {
                            popUpTo(Routes.MAIN)
                        }
                    }
                )
            }
        }

        composable(
            route = Routes.REGISTER_SUCCESS,
            arguments = listOf(
                navArgument(Routes.ARG_NAME) { type = NavType.StringType },
                navArgument(Routes.ARG_NICKNAME) { type = NavType.StringType }
            )
        ) { backStackEntry ->
            val name = backStackEntry.arguments?.getString(Routes.ARG_NAME).orEmpty()
            val nickname = backStackEntry.arguments?.getString(Routes.ARG_NICKNAME).orEmpty()
            AppScaffold(title = "등록 완료", onNavigateHome = ::goHome, onShowAbout = ::showAbout) { padding ->
                RegisterSuccessScreen(
                    padding = padding,
                    nickname = nickname,
                    onConfirm = {
                        navController.navigate(Routes.profile(name)) {
                            popUpTo(Routes.MAIN)
                        }
                    }
                )
            }
        }

        composable(
            route = Routes.PROFILE,
            arguments = listOf(navArgument(Routes.ARG_NAME) { type = NavType.StringType })
        ) { backStackEntry ->
            val name = backStackEntry.arguments?.getString(Routes.ARG_NAME).orEmpty()
            val viewModel: ProfileViewModel = viewModel()
            AppScaffold(title = "얼굴 인식 완료", onNavigateHome = ::goHome, onShowAbout = ::showAbout) { padding ->
                ProfileScreen(
                    padding = padding,
                    name = name,
                    viewModel = viewModel,
                    onViewHistory = { navController.navigate(Routes.history(name)) }
                )
            }
        }

        composable(
            route = Routes.HISTORY,
            arguments = listOf(navArgument(Routes.ARG_NAME) { type = NavType.StringType })
        ) { backStackEntry ->
            val name = backStackEntry.arguments?.getString(Routes.ARG_NAME).orEmpty()
            val viewModel: HistoryViewModel = viewModel()
            AppScaffold(title = "전체기록", onNavigateHome = ::goHome, onShowAbout = ::showAbout) { padding ->
                HistoryScreen(padding = padding, name = name, viewModel = viewModel)
            }
        }
    }
}
