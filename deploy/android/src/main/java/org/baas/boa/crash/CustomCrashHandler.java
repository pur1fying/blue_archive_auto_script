package org.baas.boa.crash;

import android.app.Application;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.os.Process;
import android.util.Log;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.io.StringWriter;

public class CustomCrashHandler implements Thread.UncaughtExceptionHandler {
    private final Thread.UncaughtExceptionHandler defaultHandler;
    private final Context context;

    public CustomCrashHandler(Context context) {
        this.context = context;
        this.defaultHandler = Thread.getDefaultUncaughtExceptionHandler();
    }

    @Override
    public void uncaughtException(Thread thread, Throwable ex) {
        try {
            StringBuilder report = new StringBuilder();

            // 1. 基本信息
            report.append("------- DEVICE INFO -------\n");
            report.append("Model: ").append(Build.MODEL).append("\n");
            report.append("Brand: ").append(Build.BRAND).append("\n");
            report.append("Android Ver: ").append(Build.VERSION.RELEASE).append("\n");
            report.append("SDK: ").append(Build.VERSION.SDK_INT).append("\n");

            // 2. Java Stack Trace
            report.append("\n------- JAVA STACK TRACE -------\n");
            StringWriter sw = new StringWriter();
            PrintWriter pw = new PrintWriter(sw);
            ex.printStackTrace(pw);
            report.append(sw.toString());

            // 3. Logcat (这是捕获 Python traceback 的关键)
            report.append("\n------- LOGCAT TAIL (Includes Python Logs) -------\n");
            try {
                // 获取最近的 500 行日志
                java.lang.Process process = Runtime.getRuntime().exec("logcat -d -t 500 -v threadtime");
                BufferedReader bufferedReader = new BufferedReader(
                        new InputStreamReader(process.getInputStream()));

                String line;
                while ((line = bufferedReader.readLine()) != null) {
                    report.append(line).append("\n");
                }
            } catch (Exception e) {
                report.append("Failed to capture logcat: ").append(e.getMessage());
            }

            // 4. 启动 CrashActivity
            Intent intent = new Intent(context, CrashActivity.class);
            intent.putExtra(CrashActivity.EXTRA_CRASH_INFO, report.toString());
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
            context.startActivity(intent);

            // 必须杀掉当前进程，否则可能处于假死状态
            android.os.Process.killProcess(android.os.Process.myPid());
            System.exit(10);

        } catch (Exception e) {
            Log.e("CustomCrashHandler", "Error in handler", e);
            // 如果处理 crash 的逻辑也崩了，回退到系统默认
            if (defaultHandler != null) {
                defaultHandler.uncaughtException(thread, ex);
            }
        }
    }
}