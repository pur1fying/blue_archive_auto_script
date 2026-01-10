package org.baas.boa;

/**
 * 用于接收 execStream 的流式输出回调。
 */
interface IStreamCallback {
    /** 标准输出每行 */
    void onStdout(String line);

    /** 标准错误每行 */
    void onStderr(String line);

    /** 进程结束，返回退出码 */
    void onDone(int exitCode);
}


