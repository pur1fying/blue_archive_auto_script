package org.baas.boa;

import android.os.RemoteException;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;

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
    public String exec(String command) throws RemoteException {
        StringBuilder stringBuilder = new StringBuilder();
        try {
            // 执行shell命令
            Process process = Runtime.getRuntime().exec(command);
            // 读取执行结果
            InputStreamReader inputStreamReader = new InputStreamReader(process.getInputStream());
            BufferedReader bufferedReader = new BufferedReader(inputStreamReader);
            String line;
            while ((line = bufferedReader.readLine()) != null) {
                stringBuilder.append(line).append("\n");
            }
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        return stringBuilder.toString();
    }
}
