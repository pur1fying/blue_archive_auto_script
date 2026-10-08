package org.baas.boa.crash;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import androidx.core.content.FileProvider; // 需要在 build.gradle 引入 androidx

import java.io.*;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

public class CrashActivity extends Activity {
    public static final String EXTRA_CRASH_INFO = "crashInfo";
    private String crashLogContent = "";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // 简单的 UI 构建 (也可以用 layout xml)
        ScrollView scrollView = new ScrollView(this);
        android.widget.LinearLayout layout = new android.widget.LinearLayout(this);
        layout.setOrientation(android.widget.LinearLayout.VERTICAL);
        scrollView.addView(layout);

        Button btnShare = new Button(this);
        btnShare.setText("Share Crash Report (ZIP)");
        
        TextView tvLog = new TextView(this);
        tvLog.setTextSize(12);
        
        layout.addView(btnShare);
        layout.addView(tvLog);
        setContentView(scrollView);

        // 获取传递过来的崩溃信息
        crashLogContent = getIntent().getStringExtra(EXTRA_CRASH_INFO);
        if (crashLogContent == null) crashLogContent = "No crash data found.";
        tvLog.setText(crashLogContent);

        btnShare.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                shareCrashZip();
            }
        });
    }

    private void shareCrashZip() {
        try {
            // 1. 创建临时文件目录
            File cacheDir = new File(getExternalCacheDir(), "crash_reports");
            if (!cacheDir.exists()) cacheDir.mkdirs();

            String timestamp = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(new Date());
            File txtFile = new File(cacheDir, "crash_" + timestamp + ".txt");
            File zipFile = new File(cacheDir, "crash_report_" + timestamp + ".zip");

            // 2. 写入文本文件
            FileWriter writer = new FileWriter(txtFile);
            writer.write(crashLogContent);
            writer.close();

            // 3. 打包成 ZIP
            zipFile(txtFile, zipFile);

            // 4. 调用系统分享
            Intent shareIntent = new Intent(Intent.ACTION_SEND);
            shareIntent.setType("application/zip");
            
            // 注意：需要 FileProvider (见下文配置)
            Uri fileUri = FileProvider.getUriForFile(
                    this, 
                    getApplicationContext().getPackageName() + ".fileprovider", 
                    zipFile);
            
            shareIntent.putExtra(Intent.EXTRA_STREAM, fileUri);
            shareIntent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            startActivity(Intent.createChooser(shareIntent, "Share Crash Report"));

        } catch (Exception e) {
            e.printStackTrace();
            Toast.makeText(this, "Failed to create zip: " + e.getMessage(), Toast.LENGTH_SHORT).show();
        }
    }

    private void zipFile(File srcFile, File zipFile) throws IOException {
        FileOutputStream fos = new FileOutputStream(zipFile);
        ZipOutputStream zos = new ZipOutputStream(fos);
        FileInputStream fis = new FileInputStream(srcFile);
        
        ZipEntry zipEntry = new ZipEntry(srcFile.getName());
        zos.putNextEntry(zipEntry);
        
        byte[] bytes = new byte[1024];
        int length;
        while ((length = fis.read(bytes)) >= 0) {
            zos.write(bytes, 0, length);
        }
        
        zos.closeEntry();
        fis.close();
        zos.close();
        fos.close();
    }
}