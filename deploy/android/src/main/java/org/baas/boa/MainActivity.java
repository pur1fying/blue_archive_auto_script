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
import java.util.List;
import java.util.ArrayList;

import org.kivy.android.PythonActivity;
import org.baas.boa.crash.CustomCrashHandler;
import com.benjaminwan.ocrlibrary.OcrEngine;

public class MainActivity extends PythonActivity {

    private static final String TAG = "MainActivity";
    private boolean isDebugMode = false;
    private String mDebugRoot = null;

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
}