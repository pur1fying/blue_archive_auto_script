package org.baas.boa;

import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.util.Log;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.TextView;
import java.io.File;

import org.kivy.android.PythonActivity;
import org.baas.boa.crash.CustomCrashHandler;

public class MainActivity extends PythonActivity {

    private static final String TAG = "MainActivity";
    private boolean isDebugMode = false;
    private String mDebugRoot = null;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        // 1. 注册崩溃监听 (最先执行)
        Thread.setDefaultUncaughtExceptionHandler(new CustomCrashHandler(this));

        // 2. 预先检测 SD 卡调试目录
        checkDebugMode();

        // 3. 执行父类逻辑
        // 注意：父类会调用 getAppRoot() 进行解压。
        // 我们不重写 getAppRoot() 或者让它返回内部路径，
        // 这样解压操作只会发生在内部存储，绝对不会覆盖 SD 卡上的文件！
        super.onCreate(savedInstanceState);

        // 4. 添加调试水印
        if (isDebugMode) {
            addDebugOverlay();
        }
    }

    /**
     * 检测是否存在 SD 卡调试代码
     */
    private void checkDebugMode() {
        File externalFiles = getExternalFilesDir(null);
        if (externalFiles != null) {
            // 你的调试代码路径：/sdcard/Android/data/org.baas.boa/files/app
            File debugAppDir = new File(externalFiles, "app");
            File debugMain = new File(debugAppDir, "main.py");

            if (debugMain.exists()) {
                isDebugMode = true;
                mDebugRoot = debugAppDir.getAbsolutePath();
                Log.w(TAG, "##### DEBUG MODE DETECTED #####");
                Log.w(TAG, "Target Root: " + mDebugRoot);
            }
        }
    }

    // ---------------------------------------------------------
    // 下面是 UI 水印部分，保持不变
    // ---------------------------------------------------------
    private void addDebugOverlay() {
        TextView debugLabel = new TextView(this);
        debugLabel.setText("DEBUG MODE (SDCARD)");
        debugLabel.setTextColor(Color.RED);
        debugLabel.setTextSize(12);
        debugLabel.setTypeface(null, Typeface.BOLD);
        debugLabel.setBackgroundColor(Color.argb(150, 0, 0, 0));
        debugLabel.setPadding(16, 8, 16, 8);

        FrameLayout.LayoutParams params = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
        );
        params.gravity = Gravity.BOTTOM | Gravity.END;
        params.setMargins(0, 0, 20, 20);

        this.addContentView(debugLabel, params);
    }
}