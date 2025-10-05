package org.baas.boa;

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
    String exec(String command) = 2;
}
