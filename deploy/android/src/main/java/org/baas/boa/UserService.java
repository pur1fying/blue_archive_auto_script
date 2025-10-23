package org.baas.boa;

import android.os.RemoteException;
import android.util.Base64;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.nio.charset.StandardCharsets;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

public class UserService extends IUserService.Stub {

    @Override
    public void destroy() throws RemoteException {
        System.exit(0);
    }

    @Override
    public void exit() throws RemoteException {
        destroy();
    }

    @Override
    public CommandResult exec(String command) throws RemoteException {
        final StringBuilder out = new StringBuilder();
        final StringBuilder err = new StringBuilder();
        int exit = -1;
        try {
            Process process = Runtime.getRuntime().exec(command);

            Thread tOut = new Thread(() -> {
                try (BufferedReader br = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
                    String line;
                    while ((line = br.readLine()) != null) {
                        out.append(line).append("\n");
                    }
                } catch (IOException ignored) {}
            });
            Thread tErr = new Thread(() -> {
                try (BufferedReader br = new BufferedReader(new InputStreamReader(process.getErrorStream()))) {
                    String line;
                    while ((line = br.readLine()) != null) {
                        err.append(line).append("\n");
                    }
                } catch (IOException ignored) {}
            });
            tOut.start();
            tErr.start();
            exit = process.waitFor();
            tOut.join();
            tErr.join();
        } catch (Exception e) {
            err.append("exec error: ").append(e.getMessage());
        }
        CommandResult res = new CommandResult();
        res.exitCode = exit;
        res.stdout = out.toString();
        res.stderr = err.toString();
        return res;
    }

    @Override
    public void execStream(String command, IStreamCallback callback) throws RemoteException {
        new Thread(() -> {
            int exit = -1;
            try {
                Process process = Runtime.getRuntime().exec(command);

                Thread tOut = new Thread(() -> {
                    try (BufferedReader br = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
                        String line;
                        while ((line = br.readLine()) != null) {
                            try { callback.onStdout(line); } catch (RemoteException ignored) {}
                        }
                    } catch (IOException ignored) {}
                });
                Thread tErr = new Thread(() -> {
                    try (BufferedReader br = new BufferedReader(new InputStreamReader(process.getErrorStream()))) {
            String line;
                        while ((line = br.readLine()) != null) {
                            try { callback.onStderr(line); } catch (RemoteException ignored) {}
                        }
                    } catch (IOException ignored) {}
                });
                tOut.start();
                tErr.start();
                exit = process.waitFor();
                tOut.join();
                tErr.join();
            } catch (Exception e) {
                try { callback.onStderr("execStream error: " + e.getMessage()); } catch (RemoteException ignored) {}
            } finally {
                try { callback.onDone(exit); } catch (RemoteException ignored) {}
            }
        }).start();
    }

    // ================= File System =================
    @Override
    public FsStat fsStat(String path) throws RemoteException {
        File f = new File(path);
        FsStat st = new FsStat();
        st.exists = f.exists();
        st.isDir = f.isDirectory();
        st.size = f.exists() ? f.length() : 0;
        st.mtime = f.exists() ? f.lastModified() : 0;
        st.mode = null; // Cannot get directly
        st.uid = null;
        st.gid = null;
        return st;
    }

    @Override
    public String[] fsList(String path) throws RemoteException {
        File dir = new File(path);
        if (!dir.isDirectory()) return new String[0];
        String[] names = dir.list();
        return names != null ? names : new String[0];
    }

    @Override
    public FsReadResult fsRead(String path) throws RemoteException {
        try {
            File file = new File(path);
            if (!file.exists()) throw new RemoteException("File not exists: " + path);
            byte[] data = new byte[(int)Math.min(file.length(), Integer.MAX_VALUE)];
            try (FileInputStream fis = new FileInputStream(file)) {
                int offset = 0;
                int read;
                while ((read = fis.read(data, offset, data.length - offset)) > 0) {
                    offset += read;
                    if (offset == data.length) break;
                }
                if (offset < data.length) {
                    byte[] resized = new byte[offset];
                    System.arraycopy(data, 0, resized, 0, offset);
                    data = resized;
                }
            }
            String text = new String(data, StandardCharsets.UTF_8);
            boolean looksText = true;
            for (int i = 0; i < text.length(); i++) {
                int ch = text.charAt(i);
                if (!(ch == 9 || ch == 10 || ch == 13 || (ch >= 32 && ch < 0xD800) || (ch >= 0xE000 && ch <= 0xFFFD))) {
                    looksText = false; break;
                }
            }
            FsReadResult res = new FsReadResult();
            if (looksText) {
                res.isBase64 = false;
                res.text = text;
                res.bytes = null;
            } else {
                res.isBase64 = true;
                res.text = null;
                res.bytes = data;
            }
            return res;
        } catch (IOException e) {
            throw new RemoteException(e.getMessage());
        }
    }

    @Override
    public void fsWrite(String path, String content, boolean append) throws RemoteException {
        try {
            boolean isB64 = content != null && content.startsWith("b64:");
            if (isB64) {
                byte[] bytes = Base64.decode(content.substring(4), Base64.DEFAULT);
                try (FileOutputStream fos = new FileOutputStream(path, append)) {
                    fos.write(bytes);
                }
            } else {
                try (BufferedWriter bw = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(path, append), StandardCharsets.UTF_8))) {
                    bw.write(content == null ? "" : content);
                }
            }
        } catch (IOException e) {
            throw new RemoteException(e.getMessage());
        }
    }

    @Override
    public void fsDelete(String path, boolean recursive) throws RemoteException {
        File f = new File(path);
        if (!f.exists()) return;
        if (f.isDirectory() && recursive) {
            deleteRecursive(f);
        } else if (!f.delete()) {
            throw new RemoteException("Failed to delete: " + path);
        }
    }

    private void deleteRecursive(File f) throws RemoteException {
        File[] list = f.listFiles();
        if (list != null) {
            for (File c : list) {
                if (c.isDirectory()) deleteRecursive(c);
                else if (!c.delete()) throw new RemoteException("Failed to delete: " + c.getAbsolutePath());
            }
        }
        if (!f.delete()) throw new RemoteException("Failed to delete: " + f.getAbsolutePath());
    }

    @Override
    public void fsMkdirs(String path) throws RemoteException {
        File d = new File(path);
        if (!d.exists() && !d.mkdirs()) {
            throw new RemoteException("Failed to mkdirs: " + path);
        }
    }

    @Override
    public void fsMove(String src, String dst, boolean replace) throws RemoteException {
        File s = new File(src);
        File d = new File(dst);
        if (!s.exists()) throw new RemoteException("Source not exists: " + src);
        if (d.exists()) {
            if (!replace) throw new RemoteException("Dest exists: " + dst);
            if (d.isDirectory()) {
                deleteRecursive(d);
            } else if (!d.delete()) {
                throw new RemoteException("Failed to delete dest: " + dst);
            }
        }
        boolean renamed = s.renameTo(d);
        if (!renamed) {
            throw new RemoteException("Failed to move: " + src + " -> " + dst);
        }
    }

    // ================= Package Manager =================
    @Override
    public void pmInstall(String apkPath) throws RemoteException {
        String cmd = "pm install -r \"" + apkPath.replace("\"", "\\\"") + "\"";
        CommandResult res = exec(cmd);
        String out = (res.stdout == null ? "" : res.stdout);
        String err = (res.stderr == null ? "" : res.stderr);
        boolean ok = (out.toLowerCase().contains("success") || err.toLowerCase().contains("success"));
        if (!ok) throw new RemoteException("pm install failed: " + out + (err.isEmpty()?"":"\n"+err));
    }

    @Override
    public void pmUninstall(String packageName) throws RemoteException {
        String cmd = "pm uninstall " + packageName;
        CommandResult res = exec(cmd);
        String out = (res.stdout == null ? "" : res.stdout);
        String err = (res.stderr == null ? "" : res.stderr);
        boolean ok = (out.toLowerCase().contains("success") || err.toLowerCase().contains("success"));
        if (!ok) throw new RemoteException("pm uninstall failed: " + out + (err.isEmpty()?"":"\n"+err));
    }
}
