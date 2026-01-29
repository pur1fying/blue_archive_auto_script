package org.baas.boa;
import org.baas.boa.CommandResult;
import org.baas.boa.IStreamCallback;
import org.baas.boa.FsStat;
import org.baas.boa.FsReadResult;

interface IUserService {

    /**
     * Shizuku服务端定义的销毁方法
     */
    void destroy() = 16777114;

    /**
     * 自定义的退出方法
     */
    void exit() = 1;

    /**
     * 执行命令
     */
    CommandResult exec(in String[] command) = 2;

    /**
     * 以流式输出方式执行命令
     */
    void execStream(in String[] command, IStreamCallback callback) = 3;

    // ========= 文件系统 =========
    FsStat fsStat(String path) = 10;
    String[] fsList(String path) = 11;
    FsReadResult fsRead(String path) = 12;
    void fsWrite(String path, String content, boolean append) = 13;
    void fsDelete(String path, boolean recursive) = 14;
    void fsMkdirs(String path) = 15;
    void fsMove(String src, String dst, boolean replace) = 16;

    // ========= 包管理 =========
    void pmInstall(String apkPath) = 20; // 通过 pm install -r
    void pmUninstall(String packageName) = 21;
}
