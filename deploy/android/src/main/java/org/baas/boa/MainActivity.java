package org.baas.boa;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.util.Log;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.TextView;
import java.io.File;
import java.util.List;
import java.util.ArrayList;

import org.kivy.android.PythonActivity;
import org.baas.boa.crash.CustomCrashHandler;
import rikka.shizuku.Shizuku;

public class MainActivity extends PythonActivity {

    private static final String TAG = "MainActivity";
    private static final int SHIZUKU_PERMISSION_CODE = 1024;
    private boolean isDebugMode = false;
    private String mDebugRoot = null;
    private static Shizuku.OnRequestPermissionResultListener shizukuListener = null;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        Thread.setDefaultUncaughtExceptionHandler(new CustomCrashHandler(this));
        super.onCreate(savedInstanceState);
    }

    @Override
    public String getEntryPoint(String search_dir) {
        /* Get the main file (.pyc|.py) depending on if we
         * have a compiled version or not.
        */
        List<String> entryPoints = new ArrayList<String>();
        entryPoints.add("android_main.pyc");  // python 3 compiled files
        for (String value : entryPoints) {
            File mainFile = new File(search_dir + "/" + value);
            if (mainFile.exists()) {
                return value;
            }
        }
        return "android_main.py";
    }

    public static void requestShizukuPermission() {
        requestShizukuPermission(PythonActivity.mActivity);
    }

    private static void requestShizukuPermission(final Activity activity) {
        if (activity == null) {
            return;
        }

        try {
            if (Shizuku.checkSelfPermission() == PackageManager.PERMISSION_GRANTED) {
                clearShizukuListener();
                return;
            }

            if (Shizuku.isPreV11()) {
                return;
            }

            if (shizukuListener == null) {
                shizukuListener = new Shizuku.OnRequestPermissionResultListener() {
                    @Override
                    public void onRequestPermissionResult(int requestCode, int grantResult) {
                        if (grantResult == PackageManager.PERMISSION_GRANTED) {
                            clearShizukuListener();
                            return;
                        }
                        showAllowDialog(activity);
                    }
                };
                Shizuku.addRequestPermissionResultListener(shizukuListener);
            }

            Shizuku.requestPermission(SHIZUKU_PERMISSION_CODE);
        } catch (Exception e) {
            showFatalDialog(activity, e);
        }
    }

    private static void clearShizukuListener() {
        if (shizukuListener != null) {
            try {
                Shizuku.removeRequestPermissionResultListener(shizukuListener);
            } catch (Exception ignored) {
            }
            shizukuListener = null;
        }
    }

    private static void showAllowDialog(final Activity activity) {
        activity.runOnUiThread(() -> {
            try {
                new AlertDialog.Builder(activity)
                    .setMessage("请允许 Shizuku 权限申请。")
                    .setCancelable(false)
                    .setPositiveButton("确定", new DialogInterface.OnClickListener() {
                        @Override
                        public void onClick(DialogInterface dialog, int which) {
                            dialog.dismiss();
                            try {
                                Shizuku.requestPermission(SHIZUKU_PERMISSION_CODE);
                            } catch (Exception e) {
                                showFatalDialog(activity, e);
                            }
                        }
                    })
                    .show();
            } catch (Exception e) {
                showFatalDialog(activity, e);
            }
        });
    }

    private static void showFatalDialog(final Activity activity, final Exception error) {
        activity.runOnUiThread(() -> {
            try {
                new AlertDialog.Builder(activity)
                    .setMessage(error.getMessage() + "\n请检查 Shizuku 服务是否正常运行。")
                    .setCancelable(false)
                    .setPositiveButton("确定", new DialogInterface.OnClickListener() {
                        @Override
                        public void onClick(DialogInterface dialog, int which) {
                            dialog.dismiss();
                            clearShizukuListener();
                            activity.finishAffinity();
                            System.exit(1);
                        }
                    })
                    .show();
            } catch (Exception e) {
                clearShizukuListener();
                activity.finishAffinity();
                System.exit(1);
            }
        });
    }
}
